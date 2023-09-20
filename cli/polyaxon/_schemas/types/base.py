from polyaxon._schemas.base import BaseSchemaModel


class BaseTypeConfig(BaseSchemaModel):
    def to_param(self):
        return self.to_dict()
