import sys
import time

import click


@click.command()
@click.option("--uuid", help="The operation's run uuid.")
@click.option(
    "--kind",
    help="The operation kind.",
)
@click.option(
    "--max-retries",
    type=int,
    default=10,
    help="Number of times to retry the process.",
)
def wait(uuid: str, kind: str, max_retries: int):
    """Delete an s3 subpath."""
    from polyaxon import settings
    from polyaxon._k8s.executor.executor import Executor

    executor = Executor(namespace=settings.CLIENT_CONFIG.namespace, in_cluster=True)
    retry = 0
    while retry < max_retries:
        if retry:
            time.sleep(retry**2)
        try:
            k8s_operation = executor.get(run_uuid=uuid, run_kind=kind)
        except Exception:  # noqa
            k8s_operation = None
        if k8s_operation:
            retry += 1
        else:
            return

    sys.exit(1)
