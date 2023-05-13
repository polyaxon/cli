from typing import Optional

from clipped.utils.enums import get_enum_value
from kubernetes.client import Configuration

from polyaxon import settings
from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.k8s.converter.mixins import MIXIN_MAPPING, BaseMixin


class BaseExecutor:
    def __init__(
        self,
        namespace: Optional[str] = None,
        k8s_config: Configuration = None,
        in_cluster: Optional[bool] = None,
    ):
        if in_cluster is None:
            in_cluster = settings.CLIENT_CONFIG.in_cluster

        if not namespace:
            namespace = settings.CLIENT_CONFIG.namespace

        self.namespace = namespace
        self.in_cluster = in_cluster
        self.k8s_config = k8s_config
        self._k8s_manager = None

    @staticmethod
    def _get_mixin_for_kind(kind: str) -> BaseMixin:
        m = MIXIN_MAPPING.get(kind)
        if not m:
            raise PolyaxonAgentError(
                "Agent received unrecognized kind {}".format(get_enum_value(kind))
            )
        return m

    @property
    def k8s_manager(self):
        raise NotImplementedError
