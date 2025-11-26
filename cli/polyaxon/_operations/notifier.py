from typing import Dict, Union

from polyaxon._auxiliaries import get_default_notification_container
from polyaxon._flow import (
    V1IO,
    V1Component,
    V1NotifierJob,
    V1Operation,
    V1Param,
    V1Plugins,
    V1Termination,
)


def get_notifier_operation(
    connection: str,
    backend: str,
    owner: str,
    project: str,
    run_uuid: str,
    run_name: str,
    condition: Union[str, Dict],
) -> V1Operation:
    return V1Operation(
        params={
            "backend": V1Param.model_construct(value=backend),
            "owner": V1Param.model_construct(value=owner),
            "project": V1Param.model_construct(value=project),
            "uuid": V1Param.model_construct(value=run_uuid),
            "name": V1Param.model_construct(value=run_name),
            "condition": V1Param.model_construct(value=condition),
        },
        termination=V1Termination.model_construct(max_retries=3),
        component=V1Component.model_construct(
            name="notifier",
            plugins=V1Plugins.model_construct(
                auth=False,
                collect_logs=False,
                collect_artifacts=False,
                collect_resources=False,
                auto_resume=False,
                sync_statuses=False,
                external_host=True,
            ),
            inputs=[
                V1IO.model_construct(name="backend", type="str", is_optional=False),
                V1IO.model_construct(name="owner", type="str", is_optional=False),
                V1IO.model_construct(name="project", type="str", is_optional=False),
                V1IO.model_construct(name="uuid", type="str", is_optional=False),
                V1IO.model_construct(name="name", type="str", is_optional=True),
                V1IO.model_construct(name="condition", type="dict", is_optional=True),
                V1IO.model_construct(name="connection", type="str", is_optional=True),
            ],
            run=V1NotifierJob.model_construct(
                connections=[connection],
                container=get_default_notification_container(),
            ),
        ),
    )
