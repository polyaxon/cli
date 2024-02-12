import asyncio
import os

from clipped.utils.tz import now
from kubernetes_asyncio.client.rest import ApiException

from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.getters import get_run_info
from polyaxon._env_vars.keys import ENV_KEYS_K8S_POD_ID
from polyaxon._fs.fs import (
    close_fs,
    get_artifacts_connection,
    get_async_fs_from_connection,
)
from polyaxon._fs.watcher import FSWatcher
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon._sidecar.container.intervals import get_sync_interval
from polyaxon._sidecar.container.monitors import sync_artifacts, sync_logs, sync_spec
from polyaxon._sidecar.ignore import CONTAINER_IGNORE_FOLDERS
from polyaxon.client import RunClient
from polyaxon.exceptions import PolyaxonClientException, PolyaxonContainerException
from polyaxon.logger import logger
from polyaxon.settings import CLIENT_CONFIG


async def start_sidecar(
    container_id: str,
    sleep_interval: int,
    sync_interval: int,
    monitor_outputs: bool,
    monitor_logs: bool,
    monitor_spec: bool,
):
    sync_interval = get_sync_interval(
        interval=sync_interval, sleep_interval=sleep_interval
    )
    try:
        pod_id = os.environ[ENV_KEYS_K8S_POD_ID]
    except KeyError as e:
        raise PolyaxonContainerException(
            "Please make sure that this job has been "
            "started by Polyaxon with all required context."
        ) from e

    try:
        owner, project, run_uuid = get_run_info()
    except PolyaxonClientException as e:
        raise PolyaxonContainerException(e)

    client = RunClient(owner=owner, project=project, run_uuid=run_uuid)
    k8s_manager = AsyncK8sManager(namespace=CLIENT_CONFIG.namespace, in_cluster=True)
    await k8s_manager.setup()
    pod = await k8s_manager.get_pod(pod_id, reraise=True)
    connection = get_artifacts_connection()
    fs = await get_async_fs_from_connection(connection=connection)
    if os.path.exists(ctx_paths.CONTEXT_MOUNT_FILE_WATCHER):
        fw = FSWatcher.read(ctx_paths.CONTEXT_MOUNT_FILE_WATCHER)
    else:
        fw = FSWatcher()

    retry = 0
    is_running = True
    counter = 0
    state = {
        "last_artifacts_check": None,
        "last_logs_check": None,
    }

    async def monitor():
        if monitor_spec and pod.metadata.annotations:
            await sync_spec(
                k8s_manager=k8s_manager,
                run_uuid=run_uuid,
                run_kind=pod.metadata.annotations.get("operation.polyaxon.com/kind"),
            )
        if monitor_logs:
            await sync_logs(
                run_uuid=run_uuid,
                k8s_manager=k8s_manager,
                pod=pod,
                last_time=None,
                stream=True,
                is_running=is_running,
            )
        if monitor_outputs:
            last_check = state["last_artifacts_check"]
            try:
                await sync_artifacts(
                    fs=fs,
                    fw=fw,
                    store_path=connection.store_path,
                    run_uuid=run_uuid,
                    exclude=CONTAINER_IGNORE_FOLDERS,
                )
            except Exception as e:
                logger.debug(
                    "An error occurred while syncing artifacts, Exception %s" % repr(e)
                )
            try:
                client.sync_events_summaries(
                    last_check=last_check,
                    events_path=ctx_paths.CONTEXT_MOUNT_RUN_EVENTS_FORMAT.format(
                        run_uuid
                    ),
                )
                client.sync_system_events_summaries(
                    last_check=last_check,
                    events_path=ctx_paths.CONTEXT_MOUNT_RUN_SYSTEM_RESOURCES_EVENTS_FORMAT.format(
                        run_uuid
                    ),
                )
                update_last_check = True
            except Exception as e:
                logger.debug(
                    "An error occurred while syncing events summaries, "
                    "Exception %s" % repr(e)
                )
                update_last_check = False
            if update_last_check:
                state["last_artifacts_check"] = now()

    while is_running and retry <= 3:
        await asyncio.sleep(sleep_interval)
        if retry:
            await asyncio.sleep(retry * 2)
        try:
            is_running = await k8s_manager.is_pod_running(pod_id, container_id)
        except ApiException as e:
            retry += 1
            logger.info("Exception %s" % repr(e))
            logger.info("Sleeping ...")
            continue

        logger.debug("Syncing ...")
        if is_running:
            retry = 0

        counter += 1
        if counter == sync_interval:
            counter = 0
            try:
                await monitor()
            except Exception as e:
                logger.warning("Polyaxon sidecar error: %s" % repr(e))

    await monitor()
    logger.info("Cleaning non main containers")
    if k8s_manager:
        logger.info("Cleaning k8s manager")
        await k8s_manager.close()

    logger.info("Cleaning fs connection")
    await close_fs(fs)
    # Ensures that the monitors are closed
    await asyncio.sleep(1)
