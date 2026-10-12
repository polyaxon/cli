from typing import Dict, List, Optional, Union


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
        shortcuts["ports"] = ports
    return shortcuts or None
