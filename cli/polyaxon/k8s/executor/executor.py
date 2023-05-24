from typing import Dict

from polyaxon.k8s.executor.base import BaseExecutor
from polyaxon.k8s.manager.manager import K8sManager
from polyaxon.utils.fqn_utils import get_resource_name


class Executor(BaseExecutor):
    def _get_manager(self):
        return K8sManager(
            k8s_config=self.k8s_config,
            namespace=self.namespace,
            in_cluster=self.in_cluster,
        )

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
        self.manager.delete_custom_object(
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
        self.manager.get_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
        )
