import pytest

from polyaxon._flow.run.enums import V1RunKind
from polyaxon._k8s.custom_resources import operation
from polyaxon._k8s.executor.async_executor import AsyncExecutor
from polyaxon._utils.test_utils import AsyncMock
from polyaxon.exceptions import PolyaxonAgentError


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


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_list_ops_uses_current_polyaxon_crds():
    class k8s_manager:
        list_custom_objects = AsyncMock(
            side_effect=lambda **kwargs: [{"plural": kwargs["plural"]}]
        )

    executor = AsyncExecutor()
    executor._manager = k8s_manager

    ops = await executor.list_ops(namespace="runs")

    expected_resources = [
        (operation.GROUP, operation.API_VERSION, operation.JOB_PLURAL),
        (operation.GROUP, operation.API_VERSION, operation.SERVICES_PLURAL),
        (operation.GROUP, operation.API_VERSION, operation.KFJOB_PLURAL),
        (operation.GROUP, operation.API_VERSION, operation.CLUSTER_PLURAL),
    ]
    assert ops == [{"plural": resource[2]} for resource in expected_resources]
    called_resources = [
        (call[1]["group"], call[1]["version"], call[1]["plural"])
        for call in k8s_manager.list_custom_objects.call_args_list
    ]
    assert called_resources == expected_resources
    assert operation.PLURAL not in [resource[2] for resource in called_resources]
    assert all(
        call[1]["namespace"] == "runs"
        for call in k8s_manager.list_custom_objects.call_args_list
    )
