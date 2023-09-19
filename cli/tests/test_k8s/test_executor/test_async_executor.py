import pytest

from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.k8s.executor.async_executor import AsyncExecutor
from polyaxon.polyflow.run.enums import V1RunKind
from polyaxon.utils.test_utils import AsyncMock


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_start_apply_stop_get_raises_for_non_recognized_kinds():
    executor = AsyncExecutor()

    try:
        await executor.create(run_uuid="", run_kind="foo", resource={})
    except PolyaxonAgentError:
        assert True

    try:
        await executor.apply(run_uuid="", run_kind="foo", resource={})
    except PolyaxonAgentError:
        assert True

    try:
        await executor.stop(run_uuid="", run_kind="foo")
    except PolyaxonAgentError:
        assert True

    try:
        await executor.get(run_uuid="", run_kind="foo")
    except PolyaxonAgentError:
        assert True


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_start_apply_stop_get():
    class k8s_manager:
        create_custom_object = AsyncMock()
        update_custom_object = AsyncMock()
        get_custom_object = AsyncMock()
        delete_custom_object = AsyncMock()

    executor = AsyncExecutor()
    k8s_manager.create_custom_object.return_value = ("", "")
    executor._manager = k8s_manager

    await executor.create(run_uuid="", run_kind=V1RunKind.JOB, resource={})
    assert k8s_manager.create_custom_object.call_count == 1

    await executor.apply(run_uuid="", run_kind=V1RunKind.JOB, resource={})
    assert k8s_manager.update_custom_object.call_count == 1

    await executor.stop(run_uuid="", run_kind=V1RunKind.JOB)
    assert k8s_manager.delete_custom_object.call_count == 1

    await executor.get(run_uuid="", run_kind=V1RunKind.JOB)
    assert k8s_manager.get_custom_object.call_count == 1
