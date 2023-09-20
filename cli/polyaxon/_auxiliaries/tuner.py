from typing import Optional

from polyaxon import pkg
from polyaxon._containers.names import MAIN_JOB_CONTAINER
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.k8s_schemas import V1Container


def get_default_tuner_container(
    command, bracket_iteration: Optional[int] = None
) -> V1Container:
    args = [
        "{{params.matrix.as_arg}}",
        "{{params.join.as_arg}}",
        "{{params.iteration.as_arg}}",
    ]
    if bracket_iteration is not None:
        args.append("{{params.bracket_iteration.as_arg}}")
    return V1Container(
        name=MAIN_JOB_CONTAINER,
        image="polyaxon/polyaxon-hpsearch:{}".format(pkg.VERSION),
        image_pull_policy=PullPolicy.IF_NOT_PRESENT.value,
        command=command,
        args=args,
        resources=k8s_schemas.V1ResourceRequirements(
            requests={"cpu": "0.1", "memory": "180Mi"},
        ),
    )
