import os
import pytest
import uuid

from polyaxon.env_vars.keys import ENV_KEYS_RUN_INSTANCE
from polyaxon.exceptions import PolyaxonContainerException
from polyaxon.sidecar.container import start_sidecar
from polyaxon.utils.test_utils import patch_settings


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_monitor_raise_if_no_env_is_set():
    patch_settings()
    os.environ[ENV_KEYS_RUN_INSTANCE] = "foo"
    with pytest.raises(PolyaxonContainerException):
        await start_sidecar(
            container_id="foo",
            sleep_interval=3,
            sync_interval=6,
            monitor_outputs=True,
            monitor_logs=False,
        )
    del os.environ[ENV_KEYS_RUN_INSTANCE]


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_monitor_raise_if_no_pod_id():
    patch_settings()
    os.environ[ENV_KEYS_RUN_INSTANCE] = "owner.project.runs.{}".format(uuid.uuid4().hex)
    with pytest.raises(PolyaxonContainerException):
        await start_sidecar(
            container_id="foo",
            sleep_interval=3,
            sync_interval=6,
            monitor_outputs=True,
            monitor_logs=False,
        )
    del os.environ[ENV_KEYS_RUN_INSTANCE]
