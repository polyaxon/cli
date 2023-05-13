from typing import Dict

from polyaxon.k8s.executor.base import BaseExecutor
from polyaxon.k8s.manager.async_manager import AsyncK8sManager
from polyaxon.utils.fqn_utils import get_resource_name


class AsyncExecutor(BaseExecutor):
    @property
    def k8s_manager(self):
        if not self._k8s_manager:
            self._k8s_manager = AsyncK8sManager(
                namespace=self.namespace,
                in_cluster=self.in_cluster,
            )
        return self._k8s_manager

    async def create(self, run_uuid: str, run_kind: str, resource: Dict):
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return await self.k8s_manager.create_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
            body=resource,
        )

    async def apply(self, run_uuid: str, run_kind: str, resource: Dict):
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return await self.k8s_manager.update_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
            body=resource,
        )

    async def stop(self, run_uuid: str, run_kind: str):
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return await self.k8s_manager.delete_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
        )

    async def get(self, run_uuid: str, run_kind: str):
        mixin = self._get_mixin_for_kind(kind=run_kind)
        resource_name = get_resource_name(run_uuid)
        return await self.k8s_manager.get_custom_object(
            name=resource_name,
            group=mixin.GROUP,
            version=mixin.API_VERSION,
            plural=mixin.PLURAL,
        )
