import re

from typing import Optional

from kubernetes.client import Configuration


class BaseK8sManager:
    CLIENT = None

    def __init__(self, namespace="default", in_cluster=False):
        self.namespace = namespace
        self.in_cluster = in_cluster
        self.api_client = None
        self._k8s_api = None
        self._k8s_batch_api = None
        self._k8s_apps_api = None
        self._networking_v1_beta1_api = None
        self._k8s_custom_object_api = None
        self._k8s_version_api = None

    def set_namespace(self, namespace):
        self.namespace = namespace

    @staticmethod
    def get_managed_by_polyaxon(instance: str) -> str:
        return "app.kubernetes.io/instance={},app.kubernetes.io/managed-by=polyaxon".format(
            instance
        )

    @staticmethod
    def get_core_polyaxon() -> str:
        return "app.kubernetes.io/part-of=polyaxon-core"

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

    @property
    def k8s_api(self):
        if not self._k8s_api:
            self._k8s_api = self.CLIENT.CoreV1Api(self.api_client)
        return self._k8s_api

    @property
    def k8s_batch_api(self):
        if not self._k8s_batch_api:
            self._k8s_batch_api = self.CLIENT.BatchV1Api(self.api_client)
        return self._k8s_batch_api

    @property
    def k8s_apps_api(self):
        if not self._k8s_apps_api:
            self._k8s_apps_api = self.CLIENT.AppsV1Api(self.api_client)
        return self._k8s_apps_api

    @property
    def networking_v1_beta1_api(self):
        if not self._networking_v1_beta1_api:
            self._networking_v1_beta1_api = self.CLIENT.NetworkingV1beta1Api(
                self.api_client
            )
        return self._networking_v1_beta1_api

    @property
    def k8s_custom_object_api(self):
        if not self._k8s_custom_object_api:
            self._k8s_custom_object_api = self.CLIENT.CustomObjectsApi(self.api_client)
        return self._k8s_custom_object_api

    @property
    def k8s_version_api(self):
        if not self._k8s_version_api:
            self._k8s_version_api = self.CLIENT.VersionApi(self.api_client)
        return self._k8s_version_api
