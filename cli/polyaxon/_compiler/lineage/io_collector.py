from typing import Dict, List, Optional

from clipped.utils.lists import to_list

from polyaxon._connections import V1Connection
from polyaxon._flow import V1IO, V1CompiledOperation
from polyaxon.types import IMAGE, LINEAGE_VALUES
from traceml.artifacts import V1ArtifactKind, V1RunArtifact


def collect_artifacts_from_io(
    io: V1IO, connection_by_names: Dict[str, V1Connection], is_input: bool
) -> Optional[V1RunArtifact]:
    if io.type not in LINEAGE_VALUES:
        return None

    if io.type == IMAGE:
        image = io.value
        connection = connection_by_names.get(io.connection)
        if connection and connection.schema_ and connection.schema_.url:
            image = "{}/{}".format(connection.schema_.url, image)
        return V1RunArtifact(
            name=io.name,
            kind=V1ArtifactKind.DOCKER_IMAGE,
            connection=io.connection,
            summary={"image": image},
            is_input=is_input,
        )


def collect_artifacts_from_io_section(
    io_section: List[V1IO],
    connection_by_names: Dict[str, V1Connection],
    is_input: bool,
) -> List[V1RunArtifact]:
    io_section = to_list(io_section, check_none=True)
    artifacts = [
        collect_artifacts_from_io(
            io, connection_by_names=connection_by_names, is_input=is_input
        )
        for io in io_section
    ]
    return [a for a in artifacts if a]


def collect_io_artifacts(
    compiled_operation: V1CompiledOperation,
    connection_by_names: Dict[str, V1Connection],
) -> List[V1RunArtifact]:
    connection_by_names = connection_by_names or {}
    artifacts = []
    artifacts += collect_artifacts_from_io_section(
        compiled_operation.inputs,
        connection_by_names=connection_by_names,
        is_input=True,
    )
    artifacts += collect_artifacts_from_io_section(
        compiled_operation.outputs,
        connection_by_names=connection_by_names,
        is_input=False,
    )
    return artifacts
