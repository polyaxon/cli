import sys
import time

import click

from clipped.utils.coroutine import coroutine

from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.logger import logger


@click.group()
def agent():
    pass


@agent.command()
@click.option(
    "--kind",
    type=str,
    default="k8s",
    help="The agent executor backend to use.",
)
@click.option(
    "--max-interval",
    type=int,
    help="Sleep interval between fetches (Applied only to base agent).",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Number of times to retry the process.",
)
@coroutine
async def start(kind, max_retries, max_interval):
    from polyaxon import settings
    from polyaxon._env_vars.getters import get_agent_info
    from polyaxon._runner.kinds import RunnerKind

    kind = kind or RunnerKind.K8S

    if kind == RunnerKind.K8S:
        from polyaxon._k8s.agent.async_agent import AsyncAgent
    else:
        logger.error("Received an unsupported agent kind: `{}`".format(kind))
        sys.exit(1)

    settings.CLIENT_CONFIG.set_agent_header()
    owner, agent_uuid = None, None
    try:
        owner, agent_uuid = get_agent_info()
        logger.info("Using agent with info: {}, {}".format(owner, agent_uuid))
    except PolyaxonAgentError:
        logger.info("Using base agent")

    retry = 0
    while retry < max_retries:
        if retry:
            time.sleep(5 * retry)
        try:
            async with AsyncAgent(
                owner=owner, agent_uuid=agent_uuid, max_interval=max_interval
            ) as ag:
                await ag.start()
                return
        except Exception as e:
            logger.warning("Polyaxon agent retrying, error %r", e)
            retry += 1


@agent.command()
@click.option(
    "--health-interval",
    type=int,
    help="Health interval between checks.",
)
def healthz(health_interval):
    from polyaxon._runner.agent.sync_agent import BaseSyncAgent

    if not BaseSyncAgent.pong(interval=health_interval):
        logger.warning("Polyaxon agent is not healthy!")
        sys.exit(1)
