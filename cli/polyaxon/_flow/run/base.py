from polyaxon._schemas.base import BaseSchemaModel


class BaseRun(BaseSchemaModel):
    _USE_DISCRIMINATOR = True

    def get_resources(self):
        raise NotImplementedError

    def get_all_containers(self):
        raise NotImplementedError

    def get_all_connections(self):
        raise NotImplementedError

    def get_all_init(self):
        raise NotImplementedError
