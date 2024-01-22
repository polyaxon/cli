from typing import Dict, List, Optional, Tuple

from kubernetes_asyncio import client, config
from kubernetes_asyncio.client import Configuration
from kubernetes_asyncio.client.rest import ApiException

from polyaxon._k8s.manager.base import BaseK8sManager
from polyaxon._k8s.monitor import is_pod_running
from polyaxon.exceptions import PolyaxonK8sError
from polyaxon.logger import logger


class AsyncK8sManager(BaseK8sManager):
    CLIENT = client

    @staticmethod
    async def load_config(
        in_cluster: bool = False, k8s_config: Optional[bool] = None
    ) -> Configuration:
        if not k8s_config:
            if in_cluster:
                config.load_incluster_config()
            else:
                await config.load_kube_config()
        return Configuration.get_default_copy()

    async def setup(self, k8s_config: Optional[Configuration] = None):
        if not k8s_config:
            if self.in_cluster:
                config.load_incluster_config()
            else:
                await config.load_kube_config()
            self.api_client = client.api_client.ApiClient()
        else:
            self.api_client = client.api_client.ApiClient(configuration=k8s_config)

    async def close(self):
        if self.api_client:
            await self.api_client.close()

    async def get_version(self, reraise: bool = False):
        try:
            version = await self.k8s_version_api.get_code()
            return version.to_dict()
        except ApiException as e:
            logger.error("K8S error: {}".format(e))
            if reraise:
                raise PolyaxonK8sError("Connection error: %s" % e) from e

    async def get_pod(
        self, name, reraise: bool = False, namespace: str = None
    ) -> Optional[client.V1Pod]:
        try:
            return await self.k8s_api.read_namespaced_pod(  # type: ignore[attr-defined]
                name=name, namespace=namespace or self.namespace
            )
        except ApiException as e:
            if reraise:
                raise PolyaxonK8sError("Connection error: %s" % e) from e
            return None

    async def is_pod_running(
        self, pod_id: str, container_id: str, namespace: str = None
    ) -> bool:
        event = await self.k8s_api.read_namespaced_pod_status(pod_id, namespace=namespace or self.namespace)  # type: ignore[attr-defined]
        return is_pod_running(event, container_id)

    async def _list_namespace_resource(
        self, resource_api, reraise: bool = False, namespace: str = None, **kwargs
    ) -> List:
        try:
            res = await resource_api(namespace=namespace or self.namespace, **kwargs)
            if isinstance(res, dict):
                items = res["items"]
            else:
                items = res.items
            return [p for p in items]
        except ApiException as e:
            logger.error("K8S error: {}".format(e))
            if reraise:
                raise PolyaxonK8sError("Connection error: %s" % e) from e
            return []

    async def list_pods(
        self, reraise: bool = False, namespace: str = None, **kwargs
    ) -> List[client.V1Pod]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_api.list_namespaced_pod,  # type: ignore[attr-defined]
            reraise=reraise,
            namespace=namespace,
            **kwargs,
        )

    async def list_jobs(
        self, reraise: bool = False, namespace: str = None, **kwargs
    ) -> List[client.V1Job]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_batch_api.list_namespaced_job,  # type: ignore[attr-defined]
            reraise=reraise,
            namespace=namespace,
            **kwargs,
        )

    async def list_custom_objects(
        self,
        group,
        version,
        plural,
        reraise: bool = False,
        namespace: str = None,
        **kwargs
    ) -> List:
        return await self._list_namespace_resource(
            resource_api=self.k8s_custom_object_api.list_namespaced_custom_object,  # type: ignore[attr-defined]
            reraise=reraise,
            group=group,
            version=version,
            plural=plural,
            namespace=namespace,
            **kwargs,
        )

    async def list_services(
        self, reraise: bool = False, namespace: str = None, **kwargs
    ) -> List[client.V1Service]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_api.list_namespaced_service,  # type: ignore[attr-defined]
            reraise=reraise,
            namespace=namespace,
            **kwargs,
        )

    async def list_deployments(
        self, reraise: bool = False, namespace: str = None, **kwargs
    ) -> List[client.V1Deployment]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_apps_api.list_namespaced_deployment,  # type: ignore[attr-defined]
            reraise=reraise,
            namespace=namespace,
            **kwargs,
        )

    async def create_custom_object(
        self,
        name: str,
        group: str,
        version: str,
        plural: str,
        body: Dict,
        namespace: str = None,
    ) -> Dict:
        resp = await self.k8s_custom_object_api.create_namespaced_custom_object(  # type: ignore[attr-defined]
            group=group,
            version=version,
            plural=plural,
            namespace=namespace or self.namespace,
            body=body,
        )
        logger.debug("Custom object `{}` was created".format(name))
        return resp

    async def update_custom_object(
        self,
        name: str,
        group: str,
        version: str,
        plural: str,
        body: Dict,
        namespace: str = None,
    ) -> Dict:
        resp = await self.k8s_custom_object_api.patch_namespaced_custom_object(  # type: ignore[attr-defined]
            name=name,
            group=group,
            version=version,
            plural=plural,
            namespace=namespace or self.namespace,
            body=body,
            _content_type="application/merge-patch+json",
        )
        logger.debug("Custom object `{}` was patched".format(name))
        return resp

    async def create_or_update_custom_object(
        self,
        name: str,
        group: str,
        version: str,
        plural: str,
        body: Dict,
        reraise: bool = False,
        namespace: str = None,
    ) -> Tuple[Dict, bool]:
        try:
            create = await self.create_custom_object(
                name=name,
                group=group,
                version=version,
                plural=plural,
                body=body,
                namespace=namespace,
            )
            return create, True

        except ApiException as e_create:
            try:
                update = await self.update_custom_object(
                    name=name,
                    group=group,
                    version=version,
                    plural=plural,
                    body=body,
                    namespace=namespace,
                )
                return update, False
            except ApiException as e:
                if reraise:
                    raise PolyaxonK8sError(
                        "Connection error: creation %s - update %s" % (e_create, e)
                    ) from e
                else:
                    logger.error("K8S error: {}".format(e))
        return {}, False

    async def get_custom_object(
        self,
        name: str,
        group: str,
        version: str,
        plural: str,
        reraise: bool = False,
        namespace: str = None,
    ) -> Optional[Dict]:
        try:
            return await self.k8s_custom_object_api.get_namespaced_custom_object(
                name=name,
                group=group,
                version=version,
                plural=plural,
                namespace=namespace or self.namespace,
            )
        except ApiException as e:
            if reraise:
                raise PolyaxonK8sError("Connection error: %s" % e) from e
            return None

    async def delete_custom_object(
        self,
        name: str,
        group: str,
        version: str,
        plural: str,
        reraise: bool = False,
        namespace: str = None,
    ):
        try:
            await self.k8s_custom_object_api.delete_namespaced_custom_object(
                name=name,
                group=group,
                version=version,
                plural=plural,
                namespace=namespace or self.namespace,
                body=client.V1DeleteOptions(),
            )
            logger.debug("Custom object `{}` deleted".format(name))
        except ApiException as e:
            if reraise:
                raise PolyaxonK8sError("Connection error: %s" % e) from e
            else:
                logger.debug("Custom object `{}` was not found".format(name))
