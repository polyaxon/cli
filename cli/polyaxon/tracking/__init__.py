# To keep backwards compatibility

from typing import List, Optional

from polyaxon.client import RunClient
from traceml import tracking
from traceml.tracking import *

TRACKING_RUN = None


def init(
    owner: Optional[str] = None,
    project: Optional[str] = None,
    run_uuid: Optional[str] = None,
    client: Optional[RunClient] = None,
    track_code: bool = True,
    track_env: bool = True,
    track_logs: bool = True,
    refresh_data: bool = False,
    artifacts_path: Optional[str] = None,
    collect_artifacts: Optional[str] = None,
    collect_resources: Optional[str] = None,
    is_offline: Optional[bool] = None,
    is_new: Optional[bool] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Run]:
    global TRACKING_RUN

    TRACKING_RUN = tracking.init(
        owner=owner,
        project=project,
        run_uuid=run_uuid,
        client=client,
        track_code=track_code,
        track_env=track_env,
        track_logs=track_logs,
        refresh_data=refresh_data,
        artifacts_path=artifacts_path,
        collect_artifacts=collect_artifacts,
        collect_resources=collect_resources,
        is_offline=is_offline,
        is_new=is_new,
        name=name,
        description=description,
        tags=tags,
    )
    return TRACKING_RUN


def get_or_create_run(tracking_run: Optional[Run] = None) -> Optional[Run]:
    global TRACKING_RUN

    TRACKING_RUN = tracking.get_or_create_run(tracking_run)
    return TRACKING_RUN
