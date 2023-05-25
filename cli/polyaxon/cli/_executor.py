import os
import sys

from collections import namedtuple
from typing import Dict, List, Optional

from clipped.formatting import Printer
from urllib3.exceptions import HTTPError

from polyaxon import settings
from polyaxon.cli.dashboard import get_dashboard_url
from polyaxon.cli.errors import handle_cli_error
from polyaxon.cli.operations import approve
from polyaxon.cli.operations import logs as run_logs
from polyaxon.cli.operations import shell as run_shell
from polyaxon.cli.operations import statuses
from polyaxon.cli.operations import upload as run_upload
from polyaxon.cli.utils import handle_output
from polyaxon.client import RunClient
from polyaxon.constants.globals import DEFAULT_UPLOADS_PATH
from polyaxon.constants.metadata import (
    META_COPY_ARTIFACTS,
    META_EAGER_MODE,
    META_UPLOAD_ARTIFACTS,
)
from polyaxon.exceptions import PolyaxonException
from polyaxon.managers.run import RunConfigManager
from polyaxon.polyflow import V1CompiledOperation, V1Operation
from polyaxon.runner.kinds import RunnerKind
from polyaxon.schemas import V1RunPending
from polyaxon.schemas.responses.v1_run import V1Run
from polyaxon.schemas.types import V1ArtifactsType
from polyaxon.sdk.exceptions import ApiException
from polyaxon.utils import cache


class RunWatchSpec(namedtuple("RunWatchSpec", "uuid name")):
    pass


def _execute_on_docker(response: V1Run):
    from polyaxon.docker.executor import Executor

    executor = Executor()
    if not executor.manager.check():
        raise PolyaxonException("Docker is required to run this command.")
    executor.create_from_run(response)


def execute_on_k8s(response: V1Run):
    from polyaxon.k8s.executor.executor import Executor

    if not settings.AGENT_CONFIG.namespace:
        raise PolyaxonException("Agent config requires a namespace to be set.")

    executor = Executor(namespace=settings.AGENT_CONFIG.namespace)
    if not executor.manager.get_version():
        raise PolyaxonException("Kubernetes is required to run this command.")
    executor.create_from_run(response)


def _execute_on_local_process(
    response: V1Run, conda_env: Optional[str] = None, pip_env: Optional[str] = None
):
    from polyaxon.process.executor.executor import Executor

    executor = Executor()
    if not executor.manager.check():
        raise PolyaxonException("Conda is required to run this command.")

    def _check_conda():
        from polyaxon.deploy.operators.conda import CondaOperator

        conda = CondaOperator()
        if not conda.check():
            raise PolyaxonException("Conda is required to run this command.")

        envs = conda.execute(["env", "list", "--json"], is_json=True)
        env_names = [os.path.basename(env) for env in envs["envs"]]
        if conda_env not in env_names:
            raise PolyaxonException(
                "Conda env `{}` is not installed.".format(conda_env)
            )

        # cmd_bash, cmd_args = specification.run.get_container_cmd()
        # cmd_args = ["source activate {}".format(conda_env)] + cmd_args
        # subprocess.Popen(cmd_bash + [" && ".join(cmd_args)], close_fds=True)


def execute_locally(
    response: V1Run,
    executor: RunnerKind,
    conda_env: Optional[str] = None,
    pip_env: Optional[str] = None,
):
    if not settings.AGENT_CONFIG:
        settings.set_agent_config()
        if not settings.AGENT_CONFIG.artifacts_store:
            if executor == RunnerKind.K8S:
                raise PolyaxonException("Could not resolve an agent configuration.")
            settings.AGENT_CONFIG.set_default_artifacts_store()

    if executor == RunnerKind.DOCKER:
        _execute_on_docker(response)
    elif executor == RunnerKind.K8S:
        execute_on_k8s(response)
    elif executor == RunnerKind.PROCESS:
        _execute_on_local_process(response, conda_env, pip_env)


def run(
    ctx,
    name: str,
    owner: str,
    project_name: str,
    description: str,
    tags: List[str],
    op_spec: V1Operation,
    log: bool,
    shell: bool,
    upload: bool,
    upload_to: str,
    upload_from: str,
    watch: bool,
    eager: bool,
    output: Optional[str] = None,
):
    polyaxon_client = RunClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    def get_instance_info(r):
        rn = (
            f"[white]{r.name}[/white]@[white]{r.uuid}[/white]"
            if r.name
            else "[white]{r.uuid}[/white]"
        )
        return f"[white]{owner}[/white]/[white]{project_name}[/white]:{rn}"

    def cache_run(data):
        config = polyaxon_client.client.sanitize_for_serialization(data)
        cache.cache(
            config_manager=RunConfigManager,
            config=config,
            owner=owner,
            project=project_name,
        )

    def create_run(
        is_managed: bool = True,
        meta_info: Optional[Dict] = None,
        pending: Optional[str] = None,
    ):
        try:
            response = polyaxon_client.create(
                name=name,
                description=description,
                tags=tags,
                content=op_spec,
                is_managed=is_managed,
                meta_info=meta_info,
                pending=pending,
            )
            run_url = get_dashboard_url(
                subpath="{}/{}/runs/{}".format(owner, project_name, response.uuid)
            )
            if output:
                response_data = polyaxon_client.client.sanitize_for_serialization(
                    response
                )
                response_data["url"] = run_url
                handle_output(response_data, output)
                return
            Printer.success(
                "A new run was created: {}".format(get_instance_info(response))
            )

            if not eager:
                cache_run(response)
                Printer.print(
                    "You can view this run on Polyaxon UI: {}".format(run_url)
                )
            return response
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not create a run.",
                http_messages_mapping={
                    404: "Make sure you have a project initialized in your current workdir, "
                    "otherwise you need to pass a project with `-p/--project`. "
                    "The project {}/{} does not exist.".format(owner, project_name)
                },
            )
            sys.exit(1)

    def refresh_run():
        try:
            polyaxon_client.refresh_data()
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e, message="The current eager operation does not exist anymore."
            )
            sys.exit(1)

    def delete_run():
        try:
            polyaxon_client.delete()
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e, message="The current eager operation does not exist anymore."
            )
            sys.exit(1)

    def watch_run_statuses(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(statuses, watch=True)

    def watch_run_logs(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(run_logs)

    def start_run_shell(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(run_shell)

    def upload_run(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(
            run_upload, path_to=upload_to, path_from=upload_from, sync_failure=True
        )
        ctx.invoke(approve)

    if not output:
        Printer.print("Creating a new run...")
    run_meta_info = None
    if eager:
        run_meta_info = {META_EAGER_MODE: True}
    if upload:
        upload_to = upload_to or DEFAULT_UPLOADS_PATH
        run_meta_info = run_meta_info or {}
        run_meta_info[META_UPLOAD_ARTIFACTS] = upload_to
    run_instance = create_run(
        not eager, run_meta_info, pending=V1RunPending.UPLOAD if upload else None
    )
    if not run_instance:
        return

    runs_to_watch = [RunWatchSpec(run_instance.uuid, run_instance.name)]

    build_uuid = None
    if run_instance.pending == V1RunPending.BUILD and run_instance.settings.build:
        build_uuid = run_instance.settings.build.get("uuid")
        build_name = run_instance.settings.build.get("name")
        runs_to_watch.insert(0, RunWatchSpec(build_uuid, build_name))

    if upload:
        upload_run(build_uuid or run_instance.uuid)

    if eager:
        from polyaxon.polyaxonfile.manager import get_eager_matrix_operations

        refresh_run()
        # Prepare artifacts
        run_meta_info = {}
        if upload:
            run_meta_info = {
                META_UPLOAD_ARTIFACTS: upload_to,
                META_COPY_ARTIFACTS: V1ArtifactsType(
                    dirs=[run_instance.uuid]
                ).to_dict(),
            }
        compiled_operation = V1CompiledOperation.read(polyaxon_client.run_data.content)
        matrix_content = polyaxon_client.run_data.raw_content
        # Delete matrix placeholder
        Printer.print("Cleaning matrix run placeholder...")
        delete_run()
        # Suggestions
        Printer.print("Starting eager mode...")
        for op_spec in get_eager_matrix_operations(
            content=matrix_content,
            compiled_operation=compiled_operation,
            is_cli=True,
        ):
            i_run_instance = create_run(meta_info=run_meta_info)
            runs_to_watch.append(RunWatchSpec(i_run_instance.uuid, i_run_instance.name))

        return

    # Check if we need to invoke logs
    if not eager:
        if watch:
            for instance in runs_to_watch:
                Printer.header(f"Starting watch for run: {get_instance_info(instance)}")
                watch_run_statuses(instance.uuid)
        if log:
            for instance in runs_to_watch:
                Printer.header(f"Starting logs for run: {get_instance_info(instance)}")
                watch_run_logs(instance.uuid)
        if shell:
            for instance in runs_to_watch:
                Printer.header(
                    f"Starting shell session for run: {get_instance_info(instance)}",
                )
                start_run_shell(instance.uuid)
