from typing import Any, Dict, Optional, Union

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import RefField
from clipped.utils.versions import clean_version_post_suffix

from polyaxon import pkg
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._k8s import k8s_schemas
from polyaxon._schemas.base import BaseSchemaModel


def get_tmux_resources() -> k8s_schemas.V1ResourceRequirements:
    return k8s_schemas.V1ResourceRequirements(
        limits={"cpu": "100m", "memory": "64Mi"},
        requests={"cpu": "50m", "memory": "32Mi"},
    )


class V1PolyaxonTmuxContainer(BaseSchemaModel):
    _IDENTIFIER = "tmux"

    image: Optional[StrictStr] = None
    image_tag: Optional[StrictStr] = Field(alias="imageTag", default=None)
    image_pull_policy: Optional[PullPolicy] = Field(
        alias="imagePullPolicy", default=None
    )
    resources: Optional[Union[Dict[str, Any], RefField]] = None

    def get_image(self):
        image = self.image or "polyaxon/polyaxon-tmux"
        image_tag = (
            self.image_tag
            if self.image_tag is not None
            else clean_version_post_suffix(pkg.VERSION)
        )
        return "{}:{}".format(image, image_tag) if image_tag else image

    def get_resources(self):
        return self.resources if self.resources else get_tmux_resources()


def get_default_tmux_container(
    schema=True,
) -> Union[Dict, V1PolyaxonTmuxContainer]:
    default = {
        "image": "polyaxon/polyaxon-tmux",
        "imageTag": clean_version_post_suffix(pkg.VERSION),
        "imagePullPolicy": PullPolicy.IF_NOT_PRESENT.value,
        "resources": {
            "limits": {"cpu": "100m", "memory": "64Mi"},
            "requests": {"cpu": "50m", "memory": "32Mi"},
        },
    }
    if schema:
        return V1PolyaxonTmuxContainer.from_dict(default)
    return default
