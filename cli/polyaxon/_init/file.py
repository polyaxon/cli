import os

from typing import Dict

from polyaxon._client.init import get_client_or_raise
from traceml.artifacts import V1ArtifactKind


def create_file_lineage(filepath: str, summary: Dict, kind: str):
    if not filepath:
        return
    filename = os.path.basename(filepath)
    if not kind:
        if "dockerfile" in filename.lower():
            kind = V1ArtifactKind.DOCKERFILE
        else:
            kind = V1ArtifactKind.FILE

    run_client = get_client_or_raise()
    if not run_client:
        return

    run_client.log_artifact_ref(
        path=filepath,
        kind=kind,
        name=filename,
        summary=summary,
        is_input=True,
    )
