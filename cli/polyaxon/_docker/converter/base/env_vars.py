import os

from typing import Any, Iterable, List, Optional

import orjson

from clipped.utils.enums import get_enum_value
from clipped.utils.json import orjson_dumps, orjson_loads
from clipped.utils.lists import to_list

from polyaxon import settings
from polyaxon._connections import V1ConnectionResource
from polyaxon._docker import docker_types
from polyaxon._env_vars.keys import (
    ENV_KEYS_API_VERSION,
    ENV_KEYS_AUTH_TOKEN,
    ENV_KEYS_AUTHENTICATION_TYPE,
    ENV_KEYS_HAS_PROCESS_SIDECAR,
    ENV_KEYS_HEADER,
    ENV_KEYS_HEADER_SERVICE,
    ENV_KEYS_HOST,
    ENV_KEYS_IS_MANAGED,
    ENV_KEYS_K8S_NAMESPACE,
    ENV_KEYS_K8S_NODE_NAME,
    ENV_KEYS_K8S_POD_ID,
    ENV_KEYS_LOG_LEVEL,
    ENV_KEYS_SECRET_INTERNAL_TOKEN,
    ENV_KEYS_SECRET_KEY,
)
from polyaxon._runner.converter import BaseConverter
from polyaxon._services.headers import PolyaxonServiceHeaders
from polyaxon.api import VERSION_V1
from polyaxon.exceptions import PolyaxonConverterError


class EnvMixin(BaseConverter):
    @staticmethod
    def _get_env_var(name: str, value: Any) -> docker_types.V1EnvVar:
        if not isinstance(value, str):
            try:
                value = orjson_dumps(value)
            except (ValueError, TypeError) as e:
                raise PolyaxonConverterError(e)

        return docker_types.V1EnvVar(__root__=(name, value))

    @staticmethod
    def _get_from_json_resource(
        resource: V1ConnectionResource,
    ) -> List[docker_types.V1EnvVar]:
        if not resource or resource.items or resource.mount_path:
            return []

        secret = os.environ.get(resource.name)
        if not secret:
            return []
        try:
            secret_value = orjson_loads(secret)
        except Exception as e:
            raise PolyaxonConverterError from e

        return [docker_types.V1EnvVar(__root__=k) for k in (secret_value.items())]

    @classmethod
    def _get_env_from_json_resources(
        cls,
        resources: Iterable[V1ConnectionResource],
    ) -> List[docker_types.V1EnvVar]:
        resources = resources or []
        results = []
        for resource in resources:
            results += cls._get_from_json_resource(resource=resource)
        return [r for r in results if r]

    @staticmethod
    def _get_item_from_json_resource(
        key: str, resource_ref_name: str
    ) -> Optional[docker_types.V1EnvVar]:
        secret = os.environ.get(resource_ref_name)
        if not secret:
            return None
        try:
            secret_value = orjson_loads(secret)
        except orjson.JSONDecodeError:
            return docker_types.V1EnvVar(__root__=(key, secret))

        value = secret_value.get(key)
        return docker_types.V1EnvVar(__root__=(key, value))

    @classmethod
    def _get_items_from_json_resource(
        cls,
        resource: V1ConnectionResource,
    ) -> List[docker_types.V1EnvVar]:
        items_from = []
        if not resource or not resource.items:
            return items_from

        try:
            secret_value = orjson_loads(resource.name)
        except orjson.JSONDecodeError as e:
            return items_from

        for item in resource.items:
            value = secret_value.get(item)
            if value:
                items_from.append(docker_types.V1EnvVar(__root__=(item, value)))
        return items_from

    @classmethod
    def _get_env_vars_from_resources(
        cls,
        resources: Iterable[V1ConnectionResource],
    ) -> List[docker_types.V1EnvVar]:
        resources = resources or []
        env_vars = []
        for secret in resources:
            env_vars += cls._get_items_from_json_resource(resource=secret)
        return env_vars

    @classmethod
    def _get_env_vars_from_k8s_resources(
        cls,
        secrets: Iterable[V1ConnectionResource],
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[docker_types.V1EnvVar]:
        resources = to_list(secrets, check_none=True) + to_list(
            config_maps, check_none=True
        )
        return cls._get_env_vars_from_resources(resources=resources)

    @classmethod
    def _get_additional_env_vars(cls) -> List[docker_types.V1EnvVar]:
        return [cls._get_env_var(name=ENV_KEYS_HAS_PROCESS_SIDECAR, value=True)]

    @classmethod
    def _get_base_env_vars(
        cls,
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str] = None,
    ) -> List[docker_types.V1EnvVar]:
        env = [
            cls._get_env_var(name=ENV_KEYS_K8S_NODE_NAME, value="docker-agent"),
            cls._get_env_var(name=ENV_KEYS_K8S_NAMESPACE, value=namespace),
            cls._get_env_var(name=ENV_KEYS_K8S_POD_ID, value=resource_name),
        ]
        if log_level:
            env.append(cls._get_env_var(name=ENV_KEYS_LOG_LEVEL, value=log_level))
        env += cls._get_proxy_env_vars(use_proxy_env_vars_use_in_ops)
        return env

    def _get_service_env_vars(
        self,
        service_header: str,
        header: Optional[str] = PolyaxonServiceHeaders.SERVICE,
        include_secret_key: bool = False,
        include_internal_token: bool = False,
        include_agent_token: bool = False,
        authentication_type: Optional[str] = None,
        external_host: bool = False,
        log_level: Optional[str] = None,
        polyaxon_default_secret_ref: Optional[str] = None,
        polyaxon_agent_secret_ref: Optional[str] = None,
        api_version: Optional[str] = None,
        use_proxy_env_vars_use_in_ops: Optional[bool] = None,
    ) -> List[docker_types.V1EnvVar]:
        api_host = self.get_api_host(external_host)
        polyaxon_default_secret_ref = (
            polyaxon_default_secret_ref or settings.AGENT_CONFIG.app_secret_name
        )
        polyaxon_agent_secret_ref = (
            polyaxon_agent_secret_ref or settings.AGENT_CONFIG.agent_secret_name
        )
        # TODO: Add support for local CLI auth
        use_proxy_env_vars_use_in_ops = (
            use_proxy_env_vars_use_in_ops
            if use_proxy_env_vars_use_in_ops is not None
            else settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        api_version = api_version or VERSION_V1
        env_vars = self._get_base_env_vars(
            namespace=self.namespace,
            resource_name=self.resource_name,
            use_proxy_env_vars_use_in_ops=use_proxy_env_vars_use_in_ops,
        ) + [
            self._get_env_var(name=ENV_KEYS_HOST, value=api_host),
            self._get_env_var(name=ENV_KEYS_IS_MANAGED, value=True),
            self._get_env_var(name=ENV_KEYS_API_VERSION, value=api_version),
            self._get_run_instance_env_var(self.run_instance),
        ]
        if log_level:
            env_vars.append(self._get_env_var(name=ENV_KEYS_LOG_LEVEL, value=log_level))
        if header:
            env_vars.append(
                self._get_env_var(
                    name=ENV_KEYS_HEADER,
                    value=PolyaxonServiceHeaders.get_header(header),
                )
            )
        if service_header:
            env_vars += to_list(
                self._get_env_var(
                    name=ENV_KEYS_HEADER_SERVICE, value=get_enum_value(service_header)
                ),
            )
        if include_secret_key:
            env_vars += to_list(
                self._get_item_from_json_resource(
                    key=ENV_KEYS_SECRET_KEY,
                    resource_ref_name=polyaxon_default_secret_ref,
                ),
                check_none=True,
            )
        internal = False
        if include_internal_token and polyaxon_default_secret_ref:
            internal = True
            env_vars += to_list(
                self._get_item_from_json_resource(
                    key=ENV_KEYS_SECRET_INTERNAL_TOKEN,
                    resource_ref_name=polyaxon_default_secret_ref,
                ),
                check_none=True,
            )
        if include_agent_token:
            if internal:
                raise PolyaxonConverterError(
                    "A service cannot have internal token and agent token."
                )
            if polyaxon_agent_secret_ref:
                env_vars += to_list(
                    self._get_item_from_json_resource(
                        key=ENV_KEYS_AUTH_TOKEN,
                        resource_ref_name=polyaxon_agent_secret_ref,
                    ),
                    check_none=True,
                )
            elif settings.CLIENT_CONFIG.token:
                env_vars += to_list(
                    self._get_env_var(
                        name=ENV_KEYS_AUTH_TOKEN, value=settings.CLIENT_CONFIG.token
                    ),
                    check_none=True,
                )
        if authentication_type:
            env_vars += to_list(
                self._get_env_var(
                    name=ENV_KEYS_AUTHENTICATION_TYPE, value=authentication_type
                ),
                check_none=True,
            )
        return env_vars
