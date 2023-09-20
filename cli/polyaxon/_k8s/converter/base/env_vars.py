from typing import Any, Iterable, List, Optional

from clipped.utils.enums import get_enum_value
from clipped.utils.json import orjson_dumps

from polyaxon import settings
from polyaxon._connections import V1ConnectionResource
from polyaxon._env_vars.keys import (
    ENV_KEYS_API_VERSION,
    ENV_KEYS_AUTH_TOKEN,
    ENV_KEYS_AUTHENTICATION_TYPE,
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
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.common.accelerators import requests_gpu
from polyaxon._runner.converter import BaseConverter
from polyaxon._services.headers import PolyaxonServiceHeaders
from polyaxon.api import VERSION_V1
from polyaxon.exceptions import PolyaxonConverterError


class EnvMixin(BaseConverter):
    @staticmethod
    def _get_env_var(name: str, value: Any) -> k8s_schemas.V1EnvVar:
        if not isinstance(value, str):
            try:
                value = orjson_dumps(value)
            except (ValueError, TypeError) as e:
                raise PolyaxonConverterError(e)

        return k8s_schemas.V1EnvVar(name=name, value=value)

    @staticmethod
    def _get_resources_env_vars(
        resources: k8s_schemas.V1ResourceRequirements,
    ) -> List[k8s_schemas.V1EnvVar]:
        env_vars = []
        has_gpu = requests_gpu(resources)

        # Fix https://github.com/kubernetes/kubernetes/issues/59629
        # When resources.gpu.limits is not set or set to 0, we explicitly
        # pass NVIDIA_VISIBLE_DEVICES=none into container to avoid exposing GPUs.
        if not has_gpu:
            env_vars.append(
                k8s_schemas.V1EnvVar(name="NVIDIA_VISIBLE_DEVICES", value="none")
            )

        return env_vars

    @staticmethod
    def _get_from_config_map(
        key_name: str, config_map_key_name: str, config_map_ref_name: str
    ) -> k8s_schemas.V1EnvVar:
        config_map_key_ref = k8s_schemas.V1ConfigMapKeySelector(
            name=config_map_ref_name, key=config_map_key_name
        )
        value_from = k8s_schemas.V1EnvVarSource(config_map_key_ref=config_map_key_ref)
        return k8s_schemas.V1EnvVar(name=key_name, value_from=value_from)

    @staticmethod
    def _get_from_secret(
        key_name: str, secret_key_name: str, secret_ref_name: str
    ) -> k8s_schemas.V1EnvVar:
        secret_key_ref = k8s_schemas.V1SecretKeySelector(
            name=secret_ref_name, key=secret_key_name
        )
        value_from = k8s_schemas.V1EnvVarSource(secret_key_ref=secret_key_ref)
        return k8s_schemas.V1EnvVar(name=key_name, value_from=value_from)

    @classmethod
    def _get_items_from_secret(
        cls, secret: V1ConnectionResource
    ) -> List[k8s_schemas.V1EnvVar]:
        items_from = []
        if not secret or not secret.items or secret.mount_path:
            return items_from

        for item in secret.items:
            items_from.append(
                cls._get_from_secret(
                    key_name=item, secret_key_name=item, secret_ref_name=secret.name
                )
            )
        return items_from

    @classmethod
    def _get_items_from_config_map(
        cls,
        config_map: V1ConnectionResource,
    ) -> List[k8s_schemas.V1EnvVar]:
        items_from = []
        if not config_map or not config_map.items:
            return items_from

        for item in config_map.items:
            items_from.append(
                cls._get_from_config_map(
                    key_name=item,
                    config_map_key_name=item,
                    config_map_ref_name=config_map.name,
                )
            )
        return items_from

    @staticmethod
    def _get_from_field_ref(name: str, field_path: str) -> k8s_schemas.V1EnvVar:
        field_ref = k8s_schemas.V1ObjectFieldSelector(field_path=field_path)
        value_from = k8s_schemas.V1EnvVarSource(field_ref=field_ref)
        return k8s_schemas.V1EnvVar(name=name, value_from=value_from)

    @classmethod
    def _get_env_vars_from_k8s_resources(
        cls,
        secrets: Iterable[V1ConnectionResource],
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[k8s_schemas.V1EnvVar]:
        secrets = secrets or []
        config_maps = config_maps or []

        env_vars = []
        for secret in secrets:
            env_vars += cls._get_items_from_secret(secret=secret)
        for config_map in config_maps:
            env_vars += cls._get_items_from_config_map(config_map=config_map)

        return env_vars

    @classmethod
    def _get_additional_env_vars(cls) -> List[k8s_schemas.V1EnvVar]:
        return []

    @staticmethod
    def _get_env_from_secret(
        secret: V1ConnectionResource,
    ) -> Optional[k8s_schemas.V1EnvFromSource]:
        if not secret or secret.items or secret.mount_path:
            return None

        return k8s_schemas.V1EnvFromSource(secret_ref={"name": secret.name})

    @classmethod
    def _get_env_from_secrets(
        cls,
        secrets: Iterable[V1ConnectionResource],
    ) -> List[k8s_schemas.V1EnvFromSource]:
        secrets = secrets or []
        results = [cls._get_env_from_secret(secret=secret) for secret in secrets]
        return [r for r in results if r]

    @staticmethod
    def _get_env_from_config_map(
        config_map: V1ConnectionResource,
    ) -> Optional[k8s_schemas.V1EnvFromSource]:
        if not config_map or config_map.items or config_map.mount_path:
            return None

        return k8s_schemas.V1EnvFromSource(config_map_ref={"name": config_map.name})

    @classmethod
    def _get_env_from_config_maps(
        cls,
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[k8s_schemas.V1EnvFromSource]:
        config_maps = config_maps or []
        results = [
            cls._get_env_from_config_map(config_map=config_map)
            for config_map in config_maps
        ]
        return [r for r in results if r]

    @classmethod
    def _get_env_from_k8s_resources(
        cls,
        secrets: Iterable[V1ConnectionResource],
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[k8s_schemas.V1EnvFromSource]:
        secrets = secrets or []
        config_maps = config_maps or []

        env_vars = []
        env_vars += cls._get_env_from_secrets(secrets=secrets)
        env_vars += cls._get_env_from_config_maps(config_maps=config_maps)
        return env_vars

    @classmethod
    def _get_base_env_vars(
        cls,
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str] = None,
    ):
        env = [
            cls._get_from_field_ref(
                name=ENV_KEYS_K8S_NODE_NAME, field_path="spec.nodeName"
            ),
            cls._get_from_field_ref(
                name=ENV_KEYS_K8S_NAMESPACE, field_path="metadata.namespace"
            ),
            cls._get_from_field_ref(
                name=ENV_KEYS_K8S_POD_ID, field_path="metadata.name"
            ),
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
    ) -> List[k8s_schemas.V1EnvVar]:
        api_host = self.get_api_host(external_host)
        polyaxon_default_secret_ref = (
            polyaxon_default_secret_ref or settings.AGENT_CONFIG.app_secret_name
        )
        polyaxon_agent_secret_ref = (
            polyaxon_agent_secret_ref or settings.AGENT_CONFIG.agent_secret_name
        )
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
            env_vars.append(
                self._get_env_var(
                    name=ENV_KEYS_HEADER_SERVICE, value=get_enum_value(service_header)
                )
            )
        if include_secret_key:
            env_vars.append(
                self._get_from_secret(
                    key_name=ENV_KEYS_SECRET_KEY,
                    secret_key_name=ENV_KEYS_SECRET_KEY,
                    secret_ref_name=polyaxon_default_secret_ref,
                )
            )
        internal = False
        if include_internal_token and polyaxon_default_secret_ref:
            internal = True
            env_vars.append(
                self._get_from_secret(
                    ENV_KEYS_SECRET_INTERNAL_TOKEN,
                    ENV_KEYS_SECRET_INTERNAL_TOKEN,
                    secret_ref_name=polyaxon_default_secret_ref,
                )
            )
        if include_agent_token and polyaxon_agent_secret_ref:
            if internal:
                raise PolyaxonConverterError(
                    "A service cannot have internal token and agent token."
                )
            env_vars.append(
                self._get_from_secret(
                    ENV_KEYS_AUTH_TOKEN,
                    ENV_KEYS_AUTH_TOKEN,
                    secret_ref_name=polyaxon_agent_secret_ref,
                )
            )
        if authentication_type:
            env_vars.append(
                self._get_env_var(
                    name=ENV_KEYS_AUTHENTICATION_TYPE, value=authentication_type
                )
            )
        return env_vars
