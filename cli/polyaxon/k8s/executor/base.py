from typing import Dict, Optional

from kubernetes import client as k8s_client
from kubernetes.client import Configuration

from polyaxon import settings
from polyaxon.k8s.converter.converters import CONVERTERS
from polyaxon.k8s.converter.mixins import MIXIN_MAPPING
from polyaxon.runner.executor import BaseExecutor as _BaseExecutor
from polyaxon.runner.kinds import RunnerKind


class BaseExecutor(_BaseExecutor):
    MIXIN_MAPPING = MIXIN_MAPPING
    CONVERTERS = CONVERTERS
    RUNNER_KIND = RunnerKind.K8S

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

    @classmethod
    def convert(
        cls,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth: bool,
        agent_content: Optional[str] = None,
    ) -> Dict:
        resource = super(BaseExecutor, cls).convert(
            owner_name=owner_name,
            project_name=project_name,
            run_name=run_name,
            run_uuid=run_uuid,
            content=content,
            default_auth=default_auth,
        )
        api = k8s_client.ApiClient()
        return api.sanitize_for_serialization(resource)
