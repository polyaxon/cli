from typing import List, Optional

from polyaxon._auxiliaries import get_default_cleaner_container
from polyaxon._auxiliaries.cleaner import V1PolyaxonCleaner, get_batch_cleaner_container
from polyaxon._connections import V1Connection
from polyaxon._flow import (
    V1CleanerJob,
    V1Component,
    V1Environment,
    V1Operation,
    V1Plugins,
    V1Termination,
)


def get_cleaner_operation(
    connection: V1Connection,
    run_uuid: str,
    run_kind: str,
    environment: Optional[V1Environment] = None,
    cleaner: Optional[V1PolyaxonCleaner] = None,
) -> V1Operation:
    return V1Operation(
        termination=V1Termination(max_retries=1),
        component=V1Component(
            name="cleaner",
            plugins=V1Plugins(
                auth=False,
                collect_logs=False,
                collect_artifacts=False,
                collect_resources=False,
                auto_resume=False,
                sync_statuses=False,
            ),
            run=V1CleanerJob(
                environment=environment,
                connections=[connection.name],
                container=get_default_cleaner_container(
                    connection, run_uuid, run_kind, cleaner
                ),
            ),
        ),
    )


def get_batch_cleaner_operation(
    connection: V1Connection,
    paths: List[str],
    environment: Optional[V1Environment] = None,
    cleaner: Optional[V1PolyaxonCleaner] = None,
) -> V1Operation:
    return V1Operation(
        termination=V1Termination(max_retries=1),
        component=V1Component(
            name="cleaner",
            plugins=V1Plugins(
                auth=False,
                collect_logs=False,
                collect_artifacts=False,
                collect_resources=False,
                auto_resume=False,
                sync_statuses=False,
            ),
            run=V1CleanerJob(
                environment=environment,
                connections=[connection.name],
                container=get_batch_cleaner_container(connection, paths, cleaner),
            ),
        ),
    )
