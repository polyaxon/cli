from typing import Optional

from polyaxon._flow.joins import V1Join
from polyaxon._flow.matrix.bayes import V1Bayes
from polyaxon._flow.matrix.hyperband import V1Hyperband
from polyaxon._flow.matrix.matrix import V1Matrix
from polyaxon._flow.matrix.tpe import V1TPE
from polyaxon._flow.matrix.tuner import V1Tuner
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.params.params import V1Param


def get_tuner(
    tuner: V1Tuner,
    matrix: V1Matrix,
    join: V1Join,
    iteration: int,
    bracket_iteration: Optional[int] = None,
) -> V1Operation:
    params = {
        "matrix": V1Param(value=matrix.to_light_dict()),
        "iteration": V1Param(value=iteration),
    }
    if bracket_iteration is not None:
        params["bracket_iteration"] = V1Param(value=bracket_iteration)

    if tuner.params:
        params.update(tuner.params)

    return V1Operation(
        queue=tuner.queue,
        namespace=tuner.namespace,
        joins=[join],
        params=params,
        hub_ref=tuner.hub_ref,
        presets=tuner.presets,
    )


def get_bo_tuner(
    matrix: V1Bayes,
    join: V1Join,
    iteration: int,
    tuner: V1Tuner = None,
) -> V1Operation:
    tuner = tuner or V1Tuner(hub_ref="bayes-tuner")
    tuner.hub_ref = tuner.hub_ref or "bayes-tuner"
    iteration = matrix.create_iteration(iteration)
    return get_tuner(
        tuner=tuner,
        matrix=matrix,
        join=join,
        iteration=iteration,
    )


def get_hyperband_tuner(
    matrix: V1Hyperband,
    join: V1Join,
    iteration: int,
    bracket_iteration: int,
    tuner: V1Tuner = None,
) -> V1Operation:
    tuner = tuner or V1Tuner(hub_ref="hyperband-tuner")
    tuner.hub_ref = tuner.hub_ref or "hyperband-tuner"
    matrix.set_tuning_params()
    iteration, bracket_iteration = matrix.create_iteration(iteration, bracket_iteration)
    return get_tuner(
        tuner=tuner,
        matrix=matrix,
        join=join,
        iteration=iteration,
        bracket_iteration=bracket_iteration,
    )


def get_tpe_tuner(
    matrix: V1TPE,
    join: V1Join,
    iteration: int,
    tuner: V1Tuner = None,
) -> V1Operation:
    tuner = tuner or V1Tuner(hub_ref="tpe-tuner")
    tuner.hub_ref = tuner.hub_ref or "tpe-tuner"
    iteration = matrix.create_iteration(iteration)
    return get_tuner(
        tuner=tuner,
        matrix=matrix,
        join=join,
        iteration=iteration,
    )
