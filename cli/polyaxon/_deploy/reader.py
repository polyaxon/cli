from polyaxon._config.spec import ConfigSpec
from polyaxon._deploy.schemas.deployment import DeploymentConfig


def read(filepaths):
    data = ConfigSpec.read_from(filepaths)
    return DeploymentConfig.from_dict(data)
