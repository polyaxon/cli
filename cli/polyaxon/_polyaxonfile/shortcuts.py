from collections.abc import Mapping
from typing import Dict, List, Optional, Union

from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile.manager import get_op_specification
from polyaxon._polyaxonfile.specs import read_polyaxonfile
from polyaxon._polyaxonfile.specs.sections import Sections
from polyaxon.exceptions import PolyaxonfileError


SHORTCUT_KEYS = {
    Sections.SERVICE,
    Sections.CONTAINER,
    Sections.CMD,
    Sections.ENV,
    Sections.RESOURCES,
    Sections.ENVIRONMENT,
    Sections.INIT,
    Sections.CONNECTIONS,
    Sections.SIDECARS,
    Sections.VOLUMES,
}


def get_shortcuts(
    image: Optional[str] = None,
    cmd: Optional[Union[str, List[str]]] = None,
    env: Optional[Dict[str, str]] = None,
    cpu: Optional[Union[str, int, float]] = None,
    memory: Optional[Union[str, int, float]] = None,
    gpu: Optional[Union[str, int]] = None,
    ports: Optional[List[int]] = None,
) -> Optional[Dict]:
    """Root shortcuts of the given values; only `None` omits a value.

    Values are kept as given; the Polyaxonfile model validates them.
    """
    shortcuts = {}
    if image is not None:
        shortcuts["container"] = {"image": image}
    if cmd is not None:
        shortcuts["cmd"] = cmd
    if env is not None:
        shortcuts["env"] = env
    resources = {
        key: value
        for key, value in (("cpu", cpu), ("memory", memory), ("gpu", gpu))
        if value is not None
    }
    if resources:
        shortcuts["resources"] = resources
    if ports is not None:
        shortcuts["service"] = {"ports": ports}
    return shortcuts or None


def validate_shortcuts(shortcuts: Dict):
    """Validate root shortcuts as an overlay; other keys are rejected."""
    unknown = sorted(set(shortcuts) - SHORTCUT_KEYS)
    if unknown:
        raise PolyaxonfileError(
            "Received unknown shortcuts: {}.".format(", ".join(unknown))
        )
    read_polyaxonfile(shortcuts, is_preset=True)


def get_sandbox_shortcuts(shortcuts: Optional[Dict]) -> Dict:
    """A sandbox without a source is a service."""
    return {"service": {}, **(shortcuts or {})}


def get_shortcut_specification(
    content: Optional[Union[Mapping, V1Polyaxonfile]],
    shortcuts: Optional[Dict],
    sandbox: bool = False,
) -> V1Polyaxonfile:
    """Compose loaded content and shortcuts like `check_polyaxonfile`.

    Shortcuts are the final overlay of the content, or the whole source
    without it. No reads, fetches or reference collection.
    """
    if content is None:
        content = get_sandbox_shortcuts(shortcuts) if sandbox else shortcuts
        shortcuts = None
    return get_op_specification(
        config=read_polyaxonfile(content),
        preset_files=[shortcuts] if shortcuts else [],
        validate_params=False,
        sandbox=sandbox,
    )
