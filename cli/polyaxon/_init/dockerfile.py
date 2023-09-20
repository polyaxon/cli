import os

from typing import Dict

from polyaxon._client.init import get_client_or_raise
from traceml.artifacts import V1ArtifactKind


def create_dockerfile_lineage(dockerfile_path: str, summary: Dict):
    if not dockerfile_path:
        return
    filename = os.path.basename(dockerfile_path)

    run_client = get_client_or_raise()
    if not run_client:
        return

    run_client.log_artifact_ref(
        path=dockerfile_path,
        kind=V1ArtifactKind.DOCKERFILE,
        name=filename,
        summary=summary,
        is_input=True,
    )
