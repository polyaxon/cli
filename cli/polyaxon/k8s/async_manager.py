#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.=
import re

from typing import Dict, List, Optional, Tuple

from kubernetes_asyncio import client, config
from kubernetes_asyncio.client import Configuration
from kubernetes_asyncio.client.rest import ApiException

from polyaxon.exceptions import PolyaxonK8SError
from polyaxon.k8s.monitor import is_pod_running
from polyaxon.logger import logger


class AsyncK8SManager:
    def __init__(self, namespace: str = "default", in_cluster: bool = False):
        self.namespace = namespace
        self.in_cluster = in_cluster

        self.api_client = None
        self.k8s_api = None
        self.k8s_batch_api = None
        self.k8s_apps_api = None
        self.k8s_custom_object_api = None
        self.k8s_version_api = None

    @staticmethod
    def get_managed_by_polyaxon(instance: str) -> str:
        return "app.kubernetes.io/instance={},app.kubernetes.io/managed-by=polyaxon".format(
            instance
        )

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

    @classmethod
    def get_config_auth(cls, k8s_config: Optional[Configuration] = None) -> str:
        if not k8s_config or not k8s_config.api_key:
            return ""
        api_key = k8s_config.api_key
        if api_key.get("authorization", ""):
            api_key = api_key.get("authorization", "")
        elif api_key.get("BearerToken", ""):
            api_key = api_key.get("BearerToken", "")
        elif api_key.get("Authorization", ""):
            api_key = api_key.get("Authorization", "")
        elif api_key.get("Token", ""):
            api_key = api_key.get("Token", "")
        api_pattern = re.compile("bearer", re.IGNORECASE)
        return api_pattern.sub("", api_key).strip()

    async def setup(self, k8s_config: Optional[Configuration] = None):
        if not k8s_config:
            if self.in_cluster:
                config.load_incluster_config()
            else:
                await config.load_kube_config()
            self.api_client = client.api_client.ApiClient()
        else:
            self.api_client = client.api_client.ApiClient(configuration=k8s_config)

        self.k8s_api = client.CoreV1Api(self.api_client)
        self.k8s_batch_api = client.BatchV1Api(self.api_client)
        self.k8s_apps_api = client.AppsV1Api(self.api_client)
        self.k8s_custom_object_api = client.CustomObjectsApi(self.api_client)
        self.k8s_version_api = client.VersionApi(self.api_client)

    async def close(self):
        if self.api_client:
            await self.api_client.close()

    async def set_namespace(self, namespace):
        self.namespace = namespace

    async def get_pod(self, name, reraise=False) -> Optional[client.V1Pod]:
        try:
            return await self.k8s_api.read_namespaced_pod(  # type: ignore[attr-defined]
                name=name, namespace=self.namespace
            )
        except ApiException as e:
            if reraise:
                raise PolyaxonK8SError("Connection error: %s" % e) from e
            return None

    async def is_pod_running(self, pod_id: str, container_id: str) -> bool:
        event = await self.k8s_api.read_namespaced_pod_status(pod_id, self.namespace)  # type: ignore[attr-defined]
        return is_pod_running(event, container_id)

    async def _list_namespace_resource(
        self, resource_api, reraise=False, **kwargs
    ) -> List:
        try:
            res = await resource_api(namespace=self.namespace, **kwargs)
            return [p for p in res.items]
        except ApiException as e:
            logger.error("K8S error: {}".format(e))
            if reraise:
                raise PolyaxonK8SError("Connection error: %s" % e) from e
            return []

    async def list_pods(self, reraise=False, **kwargs) -> List[client.V1Pod]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_api.list_namespaced_pod,  # type: ignore[attr-defined]
            reraise=reraise,
            **kwargs,
        )

    async def list_jobs(self, reraise=False, **kwargs) -> List[client.V1Job]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_batch_api.list_namespaced_job,  # type: ignore[attr-defined]
            reraise=reraise,
            **kwargs,
        )

    async def list_custom_objects(
        self, group, version, plural, reraise=False, **kwargs
    ) -> List:
        return await self._list_namespace_resource(
            resource_api=self.k8s_custom_object_api.list_namespaced_custom_object,  # type: ignore[attr-defined]
            reraise=reraise,
            group=group,
            version=version,
            plural=plural,
            **kwargs,
        )

    async def list_services(
        self, reraise: bool = False, **kwargs
    ) -> List[client.V1Service]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_api.list_namespaced_service,  # type: ignore[attr-defined]
            reraise=reraise,
            **kwargs,
        )

    async def list_deployments(
        self, reraise: bool = False, **kwargs
    ) -> List[client.V1Deployment]:
        return await self._list_namespace_resource(
            resource_api=self.k8s_apps_api.list_namespaced_deployment,  # type: ignore[attr-defined]
            reraise=reraise,
            **kwargs,
        )

    async def create_custom_object(
        self, name: str, group: str, version: str, plural: str, body: Dict
    ) -> Dict:
        resp = await self.k8s_custom_object_api.create_namespaced_custom_object(  # type: ignore[attr-defined]
            group=group,
            version=version,
            plural=plural,
            namespace=self.namespace,
            body=body,
        )
        logger.debug("Custom object `{}` was created".format(name))
        return resp

    async def update_custom_object(
        self, name: str, group: str, version: str, plural: str, body: Dict
    ) -> Dict:
        resp = await self.k8s_custom_object_api.patch_namespaced_custom_object(  # type: ignore[attr-defined]
            name=name,
            group=group,
            version=version,
            plural=plural,
            namespace=self.namespace,
            body=body,
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
    ) -> Tuple[Dict, bool]:
        try:
            create = await self.create_custom_object(
                name=name, group=group, version=version, plural=plural, body=body
            )
            return create, True

        except ApiException as e_create:
            try:
                update = await self.update_custom_object(
                    name=name, group=group, version=version, plural=plural, body=body
                )
                return update, False
            except ApiException as e:
                if reraise:
                    raise PolyaxonK8SError(
                        "Connection error: creation %s - update %s" % (e_create, e)
                    ) from e
                else:
                    logger.error("K8S error: {}".format(e))
        return {}, False

    async def get_custom_object(
        self, name: str, group: str, version: str, plural: str, reraise: bool = False
    ) -> Optional[Dict]:
        try:
            return await self.k8s_custom_object_api.get_namespaced_custom_object(
                name=name,
                group=group,
                version=version,
                plural=plural,
                namespace=self.namespace,
            )
        except ApiException as e:
            if reraise:
                raise PolyaxonK8SError("Connection error: %s" % e) from e
            return None

    async def delete_custom_object(
        self, name: str, group: str, version: str, plural: str, reraise: bool = False
    ):
        try:
            await self.k8s_custom_object_api.delete_namespaced_custom_object(
                name=name,
                group=group,
                version=version,
                plural=plural,
                namespace=self.namespace,
                body=client.V1DeleteOptions(),
            )
            logger.debug("Custom object `{}` deleted".format(name))
        except ApiException as e:
            if reraise:
                raise PolyaxonK8SError("Connection error: %s" % e) from e
            else:
                logger.debug("Custom object `{}` was not found".format(name))
