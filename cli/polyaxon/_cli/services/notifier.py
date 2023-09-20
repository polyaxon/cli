import click

from clipped.utils.json import orjson_loads

from polyaxon._cli.options import OPTIONS_NAME


@click.command()
@click.option(
    "--backend",
    help="The notifier backend.",
)
@click.option(
    "--owner",
    help="The project owner.",
)
@click.option(
    "--project",
    help="The project containing the operation.",
)
@click.option("--uuid", help="The run uuid.")
@click.option(*OPTIONS_NAME["args"], help="The run name.")
@click.option(
    "--kind",
    help="The operation kind.",
)
@click.option(
    "--condition",
    help="The run's condition.",
)
@click.option(
    "--status",
    help="The run status.",
)
@click.option(
    "--wait-time",
    "--wait_time",
    help="The run wait_time.",
)
@click.option(
    "--duration",
    help="The run duration.",
)
@click.option(
    "--inputs",
    help="The run's inputs.",
)
@click.option(
    "--outputs",
    help="The run outputs.",
)
def notify(
    backend,
    owner,
    project,
    uuid,
    name,
    kind,
    condition,
    status,
    wait_time,
    duration,
    inputs,
    outputs,
):
    """Notifier command."""

    from polyaxon._notifiers import NOTIFIERS, NotificationSpec
    from polyaxon._schemas.lifecycle import V1StatusCondition

    condition = orjson_loads(condition)
    condition = V1StatusCondition.get_condition(**condition)
    status = status or condition.type
    notification = NotificationSpec(
        kind=kind,
        owner=owner,
        project=project,
        uuid=uuid,
        name=name,
        status=status,
        wait_time=wait_time,
        duration=duration,
        condition=condition,
        inputs=inputs,
        outputs=outputs,
    )
    NOTIFIERS[backend].execute(notification=notification)
