from typing import Dict, List

from polyaxon._compiler.lineage.io_collector import collect_io_artifacts
from polyaxon._connections import V1Connection
from polyaxon._flow import ParamSpec, V1CompiledOperation
from traceml.artifacts import V1RunArtifact


def resolve_artifacts_lineage(
    owner_name: str,
    project_name: str,
    project_uuid: str,
    run_uuid: str,
    run_name: str,
    run_path: str,
    param_spec: Dict[str, ParamSpec],
    compiled_operation: V1CompiledOperation,
    artifacts_store: V1Connection,
    connection_by_names: Dict[str, V1Connection],
) -> List[V1RunArtifact]:
    return collect_io_artifacts(
        compiled_operation=compiled_operation, connection_by_names=connection_by_names
    )
