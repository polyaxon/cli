from polyaxon._schemas.base import BaseSchemaModel


class BaseSearchConfig(BaseSchemaModel):
    _USE_DISCRIMINATOR = True

    def create_iteration(self, **kwargs) -> int:
        return 0

    def should_reschedule(self, **kwargs) -> bool:
        return False
