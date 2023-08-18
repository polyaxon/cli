from typing import Dict, Optional

from kubernetes import client as k8s_client
from kubernetes.client import Configuration

from polyaxon import settings
from polyaxon.k8s.converter.converters import CONVERTERS
from polyaxon.k8s.converter.mixins import MIXIN_MAPPING
from polyaxon.runner.executor import BaseExecutor as _BaseExecutor
from polyaxon.runner.kinds import RunnerKind
from polyaxon.utils.fqn_utils import get_resource_name


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
            agent_content=agent_content,
        )
        api = k8s_client.ApiClient()
        return api.sanitize_for_serialization(resource)

    def create(self, run_uuid: str, run_kind: str, resource: Dict) -> Dict:
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return self.manager.create_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
            body=resource,
        )

    def apply(self, run_uuid: str, run_kind: str, resource: Dict) -> Dict:
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return self.manager.update_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
            body=resource,
        )

    def stop(self, run_uuid: str, run_kind: str):
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return self.manager.delete_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
        )

    def clean(self, run_uuid: str, run_kind: str):
        return self.apply(
            run_uuid=run_uuid,
            run_kind=run_kind,
            resource={"metadata": {"finalizers": None}},
        )

    def get(self, run_uuid: str, run_kind: str):
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return self.manager.get_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
        )
