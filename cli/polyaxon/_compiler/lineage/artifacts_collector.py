import os

from typing import Optional

from polyaxon._utils.fqn_utils import to_fqn_name
from traceml.artifacts import V1ArtifactKind, V1RunArtifact


def collect_lineage_artifacts_path(artifact_path: str) -> Optional[V1RunArtifact]:
    name = os.path.basename(
        artifact_path.rstrip("/")
    )  # Trim handles cases like `foo/` -> ''
    return V1RunArtifact(
        name=to_fqn_name(name) if name else "_",
        kind=V1ArtifactKind.DIR,
        path=artifact_path,
        summary={"path": artifact_path},
        is_input=True,
    )
