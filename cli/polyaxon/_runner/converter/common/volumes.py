import uuid

from polyaxon._runner.converter.common import constants


def get_volume_name(path: str) -> str:
    name = uuid.uuid5(namespace=uuid.NAMESPACE_DNS, name=path).hex
    return constants.VOLUME_MOUNT_CONNECTIONS_FORMAT.format(name)
