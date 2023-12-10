import asyncio

import click

from clipped.utils.coroutine import coroutine

from polyaxon.logger import logger


@click.command()
@click.option(
    "--container-id",
    help="The tagged image destination $PROJECT/$IMAGE:$TAG.",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Number of times to retry the process.",
)
@click.option(
    "--sleep-interval",
    type=int,
    default=2,
    help="Sleep interval between retries in seconds.",
)
@click.option(
    "--sync-interval",
    type=int,
    default=-1,
    help="Interval between artifacts syncs in seconds.",
)
@click.option(
    "--monitor-logs",
    is_flag=True,
    default=False,
    help="Enable logs monitoring.",
)
@click.option(
    "--monitor-spec",
    is_flag=True,
    default=False,
    help="Enable spec monitoring.",
)
@coroutine
async def sidecar(
    container_id, max_retries, sleep_interval, sync_interval, monitor_logs, monitor_spec
):
    """
    Start Polyaxon's sidecar command.
    """
    from polyaxon._sidecar.container import start_sidecar

    retry = 0
    while retry < max_retries:
        if retry:
            await asyncio.sleep(retry**2)
        try:
            await start_sidecar(
                container_id=container_id,
                sleep_interval=sleep_interval,
                sync_interval=sync_interval,
                monitor_outputs=True,
                monitor_logs=monitor_logs,
                monitor_spec=monitor_spec,
            )
            return
        except Exception as e:
            logger.warning("Polyaxon sidecar retrying, error %s", e)
            retry += 1
