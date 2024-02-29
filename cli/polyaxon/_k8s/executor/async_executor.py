from typing import Any, Dict, Optional

from clipped.utils.coroutine import run_sync

from polyaxon._k8s.executor.base import BaseExecutor
from polyaxon._k8s.manager.async_manager import AsyncK8sManager


class AsyncExecutor(BaseExecutor):
    def _get_manager(self):
        return AsyncK8sManager(
            namespace=self.namespace,
            in_cluster=self.in_cluster,
        )

    async def refresh(self):
        if self._manager:
            await self._manager.close()
        manager = super().refresh()
        await manager.setup()
        return manager

    @classmethod
    async def convert(
        cls,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        content: str,
        default_auth: bool,
        agent_content: Optional[str] = None,
    ) -> Dict:
        return await run_sync(
            super(AsyncExecutor, cls).convert,
            owner_name=owner_name,
            project_name=project_name,
            run_name=run_name,
            run_uuid=run_uuid,
            content=content,
            default_auth=default_auth,
            agent_content=agent_content,
        )

    @classmethod
    async def make_and_convert(
        cls,
        owner_name: str,
        project_name: str,
        run_uuid: str,
        run_name: str,
        content: str,
        default_sa: Optional[str] = None,
        internal_auth: bool = False,
        default_auth: bool = False,
    ) -> Optional[Any]:
        return await run_sync(
            super(AsyncExecutor, cls).make_and_convert,
            owner_name=owner_name,
            project_name=project_name,
            run_uuid=run_uuid,
            run_name=run_name,
            content=content,
            default_sa=default_sa,
            internal_auth=internal_auth,
            default_auth=default_auth,
        )
