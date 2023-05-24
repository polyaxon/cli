from typing import Optional

from kubernetes.client import Configuration

from polyaxon import settings
from polyaxon.k8s.converter.mixins import MIXIN_MAPPING
from polyaxon.runner.executor import BaseExecutor as _BaseExecutor


class BaseExecutor(_BaseExecutor):
    _MIXIN_MAPPING = MIXIN_MAPPING

    def __init__(
        self,
        namespace: Optional[str] = None,
        k8s_config: Configuration = None,
        in_cluster: Optional[bool] = None,
    ):
        super().__init__()
        if in_cluster is None:
            in_cluster = settings.CLIENT_CONFIG.in_cluster

        if not namespace:
            namespace = settings.CLIENT_CONFIG.namespace

        self.namespace = namespace
        self.in_cluster = in_cluster
        self.k8s_config = k8s_config
