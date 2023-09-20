from typing import Optional

from clipped.utils.lists import to_list

from polyaxon._containers.names import generate_container_name
from polyaxon._runner.converter.types import Container


def sanitize_container_command_args(
    container: Container,
) -> Container:
    # Sanitize container command/args
    if container.command:
        container.command = [
            str(c) for c in to_list(container.command, check_none=True) if c
        ]
    if container.args:
        container.args = [str(c) for c in to_list(container.args, check_none=True) if c]

    return container


def ensure_container_name(
    container: Container, prefix: Optional[str] = None
) -> Container:
    if not container:
        return container

    name = container.name
    if not name:
        container.name = generate_container_name(prefix=prefix)
    return container
