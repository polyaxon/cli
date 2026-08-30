import time

import click

from clipped.utils.json import orjson_loads
from polyaxon.logger import logger


@click.group()
def tuner():
    logger.info("Creating new suggestions...")
    pass


@tuner.command()
@click.option(
    "--matrix",
    help="A string representing the matrix configuration for bayesian optimization.",
)
@click.option(
    "--configs",
    help="A string representing the list of configs.",
)
@click.option(
    "--metrics",
    help="A string representing the list of metrics.",
)
@click.option("--iteration", type=int, help="The current iteration.")
def bayes(matrix, configs, metrics, iteration):
    """Create suggestions based on bayesian optimization."""
    from hypertune.iteration_lineage import handle_iteration, handle_iteration_failure
    from hypertune.search_managers.bayesian_optimization.manager import (
        BayesSearchManager,
    )
    from polyaxon._client.run import RunClient
    from polyaxon._flow.matrix.bayes import V1Bayes

    matrix = V1Bayes.read(matrix)
    if configs:
        configs = orjson_loads(configs)
    if metrics:
        metrics = orjson_loads(metrics)

    client = RunClient()

    retry = 0
    exp = None
    suggestions = None
    while retry < 3:
        if retry:
            time.sleep(retry**2)
        try:
            suggestions = BayesSearchManager(
                config=matrix,
            ).get_suggestions(configs=configs, metrics=metrics)
            exp = None
            break
        except Exception as e:
            retry += 1
            logger.warning(e)
            exp = e

    if exp:
        handle_iteration_failure(client=client, exp=exp)
        return

    handle_iteration(
        client=client,
        suggestions=suggestions,
    )


@tuner.command()
@click.option(
    "--matrix", help="A string representing the matrix configuration for hyperband."
)
@click.option(
    "--configs",
    help="A string representing the list of configs.",
)
@click.option(
    "--metrics",
    help="A string representing the list of metrics.",
)
@click.option("--iteration", type=int, help="The current hyperband iteration.")
@click.option(
    "--bracket-iteration",
    "--bracket_iteration",
    type=int,
    help="The current hyperband bracket iteration.",
)
def hyperband(matrix, configs, metrics, iteration, bracket_iteration):
    """Create suggestions based on hyperband."""
    from hypertune.iteration_lineage import handle_iteration, handle_iteration_failure
    from hypertune.search_managers.hyperband.manager import HyperbandManager
    from polyaxon._client.run import RunClient
    from polyaxon._flow.matrix.hyperband import V1Hyperband

    matrix = V1Hyperband.read(matrix)
    matrix.set_tuning_params()
    if configs:
        configs = orjson_loads(configs)
    if metrics:
        metrics = orjson_loads(metrics)

    client = RunClient()

    retry = 0
    exp = None
    suggestions = None
    while retry < 3:
        if retry:
            time.sleep(retry**2)
        try:
            suggestions = HyperbandManager(config=matrix).get_suggestions(
                configs=configs,
                metrics=metrics,
                bracket_iteration=bracket_iteration,
                iteration=iteration,
            )
            exp = None
            break
        except Exception as e:
            logger.warning(e)
            exp = e

    if exp:
        handle_iteration_failure(client=client, exp=exp)
        return

    handle_iteration(
        client=client,
        suggestions=suggestions,
    )


@tuner.command()
@click.option(
    "--matrix", help="A string representing the matrix configuration for TPE."
)
@click.option(
    "--configs",
    help="A string representing the list of configs.",
)
@click.option(
    "--metrics",
    help="A string representing the list of metrics.",
)
@click.option("--iteration", type=int, help="The current iteration.")
def tpe(matrix, configs, metrics, iteration):
    """Create suggestions using native TPE."""
    from hypertune.iteration_lineage import handle_iteration, handle_iteration_failure
    from hypertune.search_managers.tpe.manager import TPEManager
    from polyaxon._client.run import RunClient
    from polyaxon._flow.matrix.tpe import V1TPE

    matrix = V1TPE.read(matrix)
    if configs:
        configs = orjson_loads(configs)
    if metrics:
        metrics = orjson_loads(metrics)

    client = RunClient()

    retry = 0
    exp = None
    suggestions = None
    while retry < 3:
        if retry:
            time.sleep(retry**2)
        try:
            suggestions = TPEManager(config=matrix).get_suggestions(
                configs=configs, metrics=metrics
            )
            exp = None
            break
        except Exception as e:
            retry += 1
            logger.warning(e)
            exp = e

    if exp:
        handle_iteration_failure(client=client, exp=exp)
        return

    handle_iteration(
        client=client,
        suggestions=suggestions,
    )
