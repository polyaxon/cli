from polyaxon.k8s.k8s_schemas import V1Container


class DestinationImageMixin:
    def apply_image_destination(self, image: str):
        self.container = self.container or V1Container()
        self.container.image = image
