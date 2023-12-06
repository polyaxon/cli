import os

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from clipped.utils.http import clean_host
from clipped.utils.lists import to_list
from vents.connections.connection_schema import patch_git

from polyaxon import settings
from polyaxon._auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon._connections import (
    CONNECTION_CONFIG,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
)
from polyaxon._containers.names import INIT_PREFIX, SIDECAR_PREFIX
from polyaxon._contexts import paths as ctx_paths
from polyaxon._docker import docker_types
from polyaxon._env_vars.keys import (
    ENV_KEYS_ARTIFACTS_STORE_NAME,
    ENV_KEYS_COLLECT_ARTIFACTS,
    ENV_KEYS_COLLECT_RESOURCES,
    ENV_KEYS_LOG_LEVEL,
    ENV_KEYS_NO_API,
    ENV_KEYS_RUN_INSTANCE,
)
from polyaxon._flow import V1CompiledOperation, V1Init, V1Plugins
from polyaxon._k8s import k8s_schemas
from polyaxon._runner.converter.common import constants
from polyaxon._runner.converter.common.containers import ensure_container_name
from polyaxon._runner.converter.common.volumes import get_volume_name
from polyaxon._runner.converter.types import (
    Container,
    ContainerPort,
    EnvVar,
    Resource,
    ResourceRequirements,
    VolumeMount,
)
from polyaxon._runner.kinds import RunnerKind
from polyaxon._schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1TensorboardType,
)
from polyaxon._services.auth import AuthenticationTypes
from polyaxon._services.headers import PolyaxonServiceHeaders
from polyaxon._services.values import PolyaxonServices
from polyaxon._utils.fqn_utils import get_resource_name, get_run_instance
from polyaxon._utils.host_utils import get_api_host
from polyaxon.exceptions import PolyaxonConverterError, PolyaxonSchemaError


class BaseConverter:
    RUNNER_KIND: RunnerKind = None
    SPEC_KIND: Optional[str] = None
    MAIN_CONTAINER_ID: Optional[str] = None

    def __init__(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        run_path: Optional[str] = None,
        namespace: str = "default",
        internal_auth: bool = False,
        polyaxon_sidecar: V1PolyaxonSidecarContainer = None,
        polyaxon_init: V1PolyaxonInitContainer = None,
        base_env_vars: bool = False,
    ):
        self.is_valid()
        self.owner_name = owner_name
        self.project_name = project_name
        self.run_name = run_name
        self.run_uuid = run_uuid
        self.run_path = run_path or self.run_uuid
        self.resource_name = self.get_resource_name()
        self.run_instance = self.get_instance()
        self.namespace = namespace
        self.internal_auth = internal_auth
        self.base_env_vars = base_env_vars
        self.polyaxon_sidecar = polyaxon_sidecar
        self.polyaxon_init = polyaxon_init

    def get_instance(self) -> str:
        return get_run_instance(
            owner=self.owner_name, project=self.project_name, run_uuid=self.run_uuid
        )

    def get_resource_name(self) -> str:
        return get_resource_name(self.run_uuid)

    def is_valid(self):
        if not self.RUNNER_KIND:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid RUNNER_KIND"
            )
        if not self.SPEC_KIND:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid SPEC_KIND"
            )
        if not self.MAIN_CONTAINER_ID:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid MAIN_CONTAINER_ID"
            )

    @staticmethod
    def get_by_name(values: List[Any]) -> Dict[str, Any]:
        return {c.name: c for c in values}

    @staticmethod
    def _post_process_host(host: str) -> str:
        return host

    @classmethod
    def get_api_host(cls, external_host: bool = False) -> str:
        if external_host:
            return cls._post_process_host(
                get_api_host(default=settings.CLIENT_CONFIG.host)
            )
        else:
            return cls._post_process_host(clean_host(settings.CLIENT_CONFIG.host))

    @staticmethod
    def filter_connections_from_init(init: List[V1Init]) -> List[V1Init]:
        return [i for i in init if i.has_connection()]

    @staticmethod
    def filter_containers_from_init(init: List[V1Init]) -> List[Container]:
        return [i.container for i in init if not i.has_connection()]

    @staticmethod
    def _sanitize_container_env(
        env: List[EnvVar],
    ) -> Optional[List[EnvVar]]:
        raise NotImplementedError

    @classmethod
    def _sanitize_container(cls, container: Container) -> Container:
        raise NotImplementedError

    @classmethod
    def _patch_container(
        cls,
        container: Container,
        name: Optional[str] = None,
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        image: Optional[str] = None,
        env: Optional[List[EnvVar]] = None,
        volume_mounts: Optional[List[VolumeMount]] = None,
        ports: Optional[List[ContainerPort]] = None,
        resources: Optional[ResourceRequirements] = None,
        **kwargs,
    ) -> k8s_schemas.V1Container:
        raise NotImplementedError

    def _get_service_env_vars(
        self,
        service_header: str,
        header: Optional[str] = None,
        include_secret_key: bool = False,
        include_internal_token: bool = False,
        include_agent_token: bool = False,
        authentication_type: Optional[str] = None,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> List[EnvVar]:
        raise NotImplementedError

    def _get_polyaxon_sidecar_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> List[EnvVar]:
        if not self.base_env_vars:
            return self._get_service_env_vars(
                service_header=PolyaxonServices.SIDECAR,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env += [self._get_env_var(name=ENV_KEYS_NO_API, value=True)]
        if log_level:
            env += [self._get_env_var(name=ENV_KEYS_LOG_LEVEL, value=log_level)]
        proxy_env = self._get_proxy_env_vars(
            settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        if proxy_env:
            env += proxy_env
        return env

    def _get_auth_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[EnvVar]]:
        if self.base_env_vars:
            return None
        return self._get_service_env_vars(
            service_header=PolyaxonServices.INITIALIZER,
            include_internal_token=self.internal_auth,
            include_agent_token=not self.internal_auth,
            authentication_type=(
                AuthenticationTypes.INTERNAL_TOKEN
                if self.internal_auth
                else AuthenticationTypes.TOKEN
            ),
            header=(
                PolyaxonServiceHeaders.INTERNAL
                if self.internal_auth
                else PolyaxonServiceHeaders.SERVICE
            ),
            external_host=external_host,
            log_level=log_level,
        )

    def _get_init_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[EnvVar]]:
        if not self.base_env_vars:
            return self._get_service_env_vars(
                service_header=PolyaxonServices.INITIALIZER,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env.append(self._get_env_var(name=ENV_KEYS_NO_API, value=True))
        if log_level:
            env.append(self._get_env_var(name=ENV_KEYS_LOG_LEVEL, value=log_level))
        proxy_env = self._get_proxy_env_vars(
            settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
        )
        if proxy_env:
            env += proxy_env
        return env

    @classmethod
    def _get_run_instance_env_var(cls, run_instance: str) -> EnvVar:
        return cls._get_env_var(name=ENV_KEYS_RUN_INSTANCE, value=run_instance)

    @staticmethod
    def _get_env_var(name: str, value: Any) -> EnvVar:
        raise NotImplementedError

    @classmethod
    def _get_connections_catalog_env_var(
        cls,
        connections: List[V1Connection],
    ) -> Optional[EnvVar]:
        catalog = CONNECTION_CONFIG.get_connections_catalog(connections)
        if not catalog:
            return None
        return cls._get_env_var(
            name=CONNECTION_CONFIG.get_connections_catalog_env_name(),
            value=catalog.to_json(),
        )

    @staticmethod
    def _get_connection_env_var(connection: V1Connection) -> List[EnvVar]:
        env_vars = []
        if not connection:
            return env_vars

        if connection.env:
            env_vars += to_list(connection.env, check_none=True)

        return env_vars

    @staticmethod
    def _get_proxy_env_var(key: str) -> Optional[str]:
        value = os.environ.get(key)
        if not value:
            value = os.environ.get(key.lower())
        if not value:
            value = os.environ.get(key.upper())

        return value

    @classmethod
    def _add_proxy_env_var(cls, name: str, value: str) -> List[EnvVar]:
        return [
            cls._get_env_var(name.upper(), value),
            cls._get_env_var(name, value),
        ]

    @classmethod
    def _get_proxy_env_vars(
        cls,
        use_proxy_env_vars_use_in_ops: bool,
    ) -> List[docker_types.V1EnvVar]:
        if use_proxy_env_vars_use_in_ops:
            env_vars = []
            https_proxy = cls._get_proxy_env_var("HTTPS_PROXY")
            if not https_proxy:
                https_proxy = cls._get_proxy_env_var("https_proxy")
            if https_proxy:
                env_vars += cls._add_proxy_env_var(
                    name="HTTPS_PROXY", value=https_proxy
                )
                env_vars += cls._add_proxy_env_var(
                    name="https_proxy", value=https_proxy
                )
            http_proxy = cls._get_proxy_env_var("HTTP_PROXY")
            if not http_proxy:
                http_proxy = cls._get_proxy_env_var("http_proxy")
            if http_proxy:
                env_vars += cls._add_proxy_env_var(name="HTTP_PROXY", value=http_proxy)
                env_vars += cls._add_proxy_env_var(name="http_proxy", value=http_proxy)
            no_proxy = cls._get_proxy_env_var("NO_PROXY")
            if not no_proxy:
                no_proxy = cls._get_proxy_env_var("no_proxy")
            if no_proxy:
                env_vars += cls._add_proxy_env_var(name="NO_PROXY", value=no_proxy)
                env_vars += cls._add_proxy_env_var(name="no_proxy", value=no_proxy)
            return env_vars
        return []

    @classmethod
    def _get_kv_env_vars(cls, kv_env_vars: List[List]) -> List[EnvVar]:
        env_vars = []
        if not kv_env_vars:
            return env_vars

        for kv_env_var in kv_env_vars:
            if not kv_env_var or not len(kv_env_var) == 2:
                raise PolyaxonConverterError(
                    "Received a wrong a key value env var `{}`".format(kv_env_var)
                )
            env_vars.append(cls._get_env_var(name=kv_env_var[0], value=kv_env_var[1]))

        return env_vars

    @classmethod
    def _get_env_vars_from_k8s_resources(
        cls,
        secrets: Iterable[V1ConnectionResource],
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[EnvVar]:
        raise NotImplementedError

    @classmethod
    def _get_additional_env_vars(cls) -> List[EnvVar]:
        raise NotImplementedError

    @staticmethod
    def _get_base_env_vars(
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str],
    ) -> List[EnvVar]:
        raise NotImplementedError

    @staticmethod
    def _new_container(name: str) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_sidecar_container(
        cls,
        container_id: str,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        env: List[EnvVar],
        artifacts_store: V1Connection,
        plugins: V1Plugins,
        run_path: Optional[str],
    ) -> Optional[Container]:
        raise NotImplementedError

    @classmethod
    def _ensure_container(
        cls, container: Container, volumes: List[k8s_schemas.V1Volume]
    ) -> docker_types.V1Container:
        raise NotImplementedError

    def _get_main_env_vars(
        self,
        plugins: V1Plugins,
        kv_env_vars: List[List],
        artifacts_store_name: str,
        connections: Iterable[V1Connection],
        secrets: Iterable[V1ConnectionResource],
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[EnvVar]:
        if self.base_env_vars:
            env = self._get_base_env_vars(
                namespace=self.namespace,
                resource_name=self.resource_name,
                use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
                log_level=plugins.log_level if plugins else None,
            )
        else:
            env = self._get_service_env_vars(
                service_header=PolyaxonServices.RUNNER,
                external_host=plugins.external_host if plugins else False,
                log_level=plugins.log_level if plugins else None,
            )
        env = to_list(env, check_none=True)
        connections = connections or []

        if plugins and plugins.collect_artifacts:
            env.append(self._get_env_var(name=ENV_KEYS_COLLECT_ARTIFACTS, value=True))

        if plugins and plugins.collect_resources:
            env.append(self._get_env_var(name=ENV_KEYS_COLLECT_RESOURCES, value=True))

        if artifacts_store_name:
            env.append(
                self._get_env_var(
                    name=ENV_KEYS_ARTIFACTS_STORE_NAME, value=artifacts_store_name
                )
            )

        # Add connections catalog env vars information
        env += to_list(
            self._get_connections_catalog_env_var(connections=connections),
            check_none=True,
        )
        # Add connection env vars information
        for connection in connections:
            try:
                env += to_list(
                    self._get_connection_env_var(connection=connection), check_none=True
                )
            except PolyaxonSchemaError as e:
                raise PolyaxonConverterError("Error resolving secrets: %s" % e) from e

        env += self._get_kv_env_vars(kv_env_vars)
        env += self._get_env_vars_from_k8s_resources(
            secrets=secrets, config_maps=config_maps
        )
        env += self._get_additional_env_vars()
        return env

    @classmethod
    def _get_docker_context_mount(cls) -> VolumeMount:
        raise NotImplementedError

    @staticmethod
    def _get_auth_context_mount(
        read_only: Optional[bool] = None,
        run_path: Optional[str] = None,
    ) -> VolumeMount:
        raise NotImplementedError

    @staticmethod
    def _get_artifacts_context_mount(
        read_only: Optional[bool] = None,
        run_path: Optional[str] = None,
    ) -> VolumeMount:
        raise NotImplementedError

    @staticmethod
    def _get_connections_context_mount(
        name: str, mount_path: str, run_path: str
    ) -> VolumeMount:
        raise NotImplementedError

    @staticmethod
    def _get_shm_context_mount() -> VolumeMount:
        raise NotImplementedError

    @classmethod
    def _get_mount_from_store(cls, store: V1Connection) -> Optional[VolumeMount]:
        raise NotImplementedError

    @staticmethod
    def _get_mount_from_resource(
        resource: V1ConnectionResource,
    ) -> Optional[VolumeMount]:
        raise NotImplementedError

    @staticmethod
    def _get_volume(host_path: str, mount_path: str, read_only: bool) -> VolumeMount:
        raise NotImplementedError

    @classmethod
    def _get_mounts(
        cls,
        use_auth_context: bool,
        use_docker_context: bool,
        use_shm_context: bool,
        use_artifacts_context: bool,
        run_path: Optional[str] = None,
    ) -> List[VolumeMount]:
        raise NotImplementedError

    @classmethod
    def _get_main_volume_mounts(
        cls,
        run_path: str,
        plugins: V1Plugins,
        init: Optional[List[V1Init]],
        connections: Iterable[V1Connection],
        secrets: Iterable[V1ConnectionResource],
        config_maps: Iterable[V1ConnectionResource],
    ) -> List[VolumeMount]:
        init = init or []
        connections = connections or []
        secrets = secrets or []
        config_maps = config_maps or []

        volume_mounts = []
        volume_names = set()
        if plugins and plugins.collect_artifacts:
            volume_mounts += to_list(
                cls._get_artifacts_context_mount(read_only=False, run_path=run_path),
                check_none=True,
            )
            volume_names.add(constants.VOLUME_MOUNT_ARTIFACTS)
        for init_connection in init:
            volume_name = (
                get_volume_name(init_connection.path)
                if init_connection.path
                else constants.VOLUME_MOUNT_ARTIFACTS
            )
            mount_path = init_connection.path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS
            if volume_name in volume_names:
                continue
            volume_names.add(volume_name)
            volume_mounts += to_list(
                cls._get_connections_context_mount(
                    name=volume_name, mount_path=mount_path, run_path=run_path
                ),
                check_none=True,
            )
        for store in connections:
            volume_mounts += to_list(
                cls._get_mount_from_store(store=store), check_none=True
            )

        for secret in secrets:
            volume_mounts += to_list(
                cls._get_mount_from_resource(resource=secret), check_none=True
            )

        for config_map in config_maps:
            volume_mounts += to_list(
                cls._get_mount_from_resource(resource=config_map), check_none=True
            )

        return volume_mounts

    def _get_main_container(
        self,
        container_id: str,
        main_container: Container,
        plugins: V1Plugins,
        artifacts_store: Optional[V1Connection],
        init: Optional[List[V1Init]],
        connections: Optional[List[str]],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        run_path: Optional[str],
        kv_env_vars: List[List] = None,
        ports: List[int] = None,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_base_store_container(
        cls,
        container: Optional[docker_types.V1Container],
        container_name: str,
        polyaxon_init: V1PolyaxonInitContainer,
        store: V1Connection,
        env: List[docker_types.V1EnvVar],
        env_from: List[k8s_schemas.V1EnvFromSource],
        volume_mounts: List[docker_types.V1VolumeMount],
        args: List[str],
        command: Optional[List[str]] = None,
    ) -> Optional[docker_types.V1Container]:
        raise NotImplementedError

    @classmethod
    def _get_custom_init_container(
        cls,
        connection: V1Connection,
        plugins: V1Plugins,
        container: Optional[Container],
        run_path: str,
        env: List[EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_dockerfile_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        dockerfile_args: V1DockerfileType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[Container] = None,
        env: List[EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_file_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        file_args: V1FileType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[Container] = None,
        env: List[EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_git_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        plugins: V1Plugins,
        run_path: str,
        container: Optional[Container] = None,
        env: List[EnvVar] = None,
        mount_path: Optional[str] = None,
        track: bool = False,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_store_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        artifacts: V1ArtifactsType,
        paths: Union[List[str], List[Tuple[str, str]]],
        run_path: str,
        container: Optional[Container] = None,
        env: List[EnvVar] = None,
        mount_path: Optional[str] = None,
        is_default_artifacts_store: bool = False,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_tensorboard_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        tb_args: V1TensorboardType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[Container] = None,
        env: List[EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_auth_context_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        run_path: str,
        env: Optional[List[EnvVar]] = None,
    ) -> Container:
        raise NotImplementedError

    @classmethod
    def _get_artifacts_path_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        run_path: str,
        auto_resume: bool,
        env: Optional[List[EnvVar]] = None,
    ) -> Container:
        raise NotImplementedError

    def _handle_init_connections(
        self,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        init_connections: List[V1Init],
        connection_by_names: Dict[str, V1Connection],
        plugins: V1Plugins,
        log_level: Optional[str] = None,
        volumes: Optional[List[k8s_schemas.V1Volume]] = None,
    ) -> List[Container]:
        containers = []
        external_host = plugins.external_host if plugins else False

        # Prepare connections that Polyaxon can init automatically
        for init_connection in init_connections:
            if init_connection.connection:
                connection_spec = connection_by_names.get(init_connection.connection)
                # Handling ssh with git
                if (
                    V1ConnectionKind.is_ssh(connection_spec.kind)
                    and init_connection.git
                ):
                    connection_spec.schema_ = patch_git(
                        connection_spec.schema_, init_connection.git
                    )
                    containers.append(
                        self._get_git_init_container(
                            run_path=self.run_path,
                            polyaxon_init=polyaxon_init,
                            connection=connection_spec,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                            track=True,
                        )
                    )
                elif V1ConnectionKind.is_git(connection_spec.kind):
                    if init_connection.git:  # Update the default schema
                        connection_spec.schema_ = patch_git(
                            connection_spec.schema_, init_connection.git
                        )
                    containers.append(
                        self._get_git_init_container(
                            run_path=self.run_path,
                            polyaxon_init=polyaxon_init,
                            connection=connection_spec,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                            track=True,
                        )
                    )
                elif V1ConnectionKind.is_artifact(connection_spec.kind):
                    containers.append(
                        self._get_store_init_container(
                            run_path=self.run_path,
                            polyaxon_init=polyaxon_init,
                            connection=connection_spec,
                            artifacts=init_connection.artifacts,
                            paths=init_connection.paths,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            is_default_artifacts_store=artifacts_store
                            and init_connection.connection == artifacts_store.name,
                        )
                    )
                else:
                    containers.append(
                        self._get_custom_init_container(
                            run_path=self.run_path,
                            connection=connection_spec,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                        )
                    )
            else:
                # artifacts init without connection should default to the artifactsStore
                if init_connection.artifacts or init_connection.paths:
                    containers.append(
                        self._get_store_init_container(
                            run_path=self.run_path,
                            polyaxon_init=polyaxon_init,
                            connection=artifacts_store,
                            artifacts=init_connection.artifacts,
                            paths=init_connection.paths,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            is_default_artifacts_store=True,
                        )
                    )
                # git init without connection
                if init_connection.git:
                    git_name = init_connection.git.get_name()
                    containers.append(
                        self._get_git_init_container(
                            run_path=self.run_path,
                            polyaxon_init=polyaxon_init,
                            connection=V1Connection(
                                name=git_name,
                                kind=V1ConnectionKind.GIT,
                                schema_=init_connection.git,
                                secret=None,
                            ),
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            plugins=plugins,
                            track=False,
                        )
                    )
                # Dockerfile initialization
                if init_connection.dockerfile:
                    containers.append(
                        self._get_dockerfile_init_container(
                            polyaxon_init=polyaxon_init,
                            dockerfile_args=init_connection.dockerfile,
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            plugins=plugins,
                            run_path=self.run_path,
                            run_instance=self.run_instance,
                        )
                    )
                # File initialization
                if init_connection.file:
                    containers.append(
                        self._get_file_init_container(
                            polyaxon_init=polyaxon_init,
                            file_args=init_connection.file,
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            plugins=plugins,
                            run_path=self.run_path,
                            run_instance=self.run_instance,
                        )
                    )
                # Tensorboard initialization
                if init_connection.tensorboard:
                    containers.append(
                        self._get_tensorboard_init_container(
                            polyaxon_init=polyaxon_init,
                            artifacts_store=artifacts_store,
                            tb_args=init_connection.tensorboard,
                            env=self._get_init_service_env_vars(
                                external_host=external_host,
                                log_level=log_level,
                            ),
                            mount_path=init_connection.path,
                            container=self._ensure_container(
                                init_connection.container, volumes=volumes
                            ),
                            plugins=plugins,
                            run_path=self.run_path,
                            run_instance=self.run_instance,
                        )
                    )

        return containers

    def get_init_containers(
        self,
        polyaxon_init: V1PolyaxonInitContainer,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        init_connections: List[V1Init],
        init_containers: List[Container],
        connection_by_names: Dict[str, V1Connection],
        log_level: Optional[str] = None,
        volumes: Optional[List[k8s_schemas.V1Volume]] = None,
    ) -> List[Container]:
        init_containers = [
            self._ensure_container(
                ensure_container_name(container=c, prefix=INIT_PREFIX), volumes=volumes
            )
            for c in to_list(init_containers, check_none=True)
        ]
        init_connections = to_list(init_connections, check_none=True)
        containers = []

        # Add auth context
        if plugins and plugins.auth:
            containers.append(
                self._get_auth_context_init_container(
                    polyaxon_init=polyaxon_init,
                    run_path=self.run_path,
                    env=self._get_auth_service_env_vars(
                        external_host=plugins.external_host
                    ),
                )
            )

        # Add outputs
        if plugins and plugins.collect_artifacts:
            containers += to_list(
                self._get_artifacts_path_init_container(
                    polyaxon_init=polyaxon_init,
                    artifacts_store=artifacts_store,
                    run_path=self.run_path,
                    auto_resume=plugins.auto_resume,
                    env=self._get_proxy_env_vars(
                        settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops
                    ),
                ),
                check_none=True,
            )

        containers += self._handle_init_connections(
            polyaxon_init=polyaxon_init,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
            plugins=plugins,
            log_level=log_level,
            volumes=volumes,
        )
        return containers + init_containers

    def get_sidecar_containers(
        self,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        sidecar_containers: List[Container],
        log_level: Optional[str] = None,
        volumes: Optional[List[k8s_schemas.V1Volume]] = None,
    ) -> List[Container]:
        sidecar_containers = [
            ensure_container_name(container=c, prefix=SIDECAR_PREFIX)
            for c in to_list(sidecar_containers, check_none=True)
        ]
        polyaxon_sidecar_container = self._get_sidecar_container(
            container_id=self.MAIN_CONTAINER_ID,
            polyaxon_sidecar=polyaxon_sidecar,
            env=self._get_polyaxon_sidecar_service_env_vars(
                external_host=plugins.external_host if plugins else False,
                log_level=log_level,
            ),
            artifacts_store=artifacts_store,
            plugins=plugins,
            run_path=self.run_path,
        )
        containers = to_list(polyaxon_sidecar_container, check_none=True)
        containers += sidecar_containers
        return [self._ensure_container(c, volumes) for c in containers]

    def get_main_container(
        self,
        main_container: Container,
        plugins: V1Plugins,
        artifacts_store: V1Connection,
        connections: List[str],
        init_connections: Optional[List[V1Init]],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        kv_env_vars: Optional[List[List]] = None,
        ports: Optional[List[int]] = None,
    ) -> Container:
        return self._get_main_container(
            container_id=self.MAIN_CONTAINER_ID,
            main_container=main_container,
            plugins=plugins,
            artifacts_store=artifacts_store,
            connections=connections,
            init=init_connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            kv_env_vars=kv_env_vars,
            ports=ports,
            run_path=self.run_path,
        )

    def get_resource(
        self,
        compiled_operation: V1CompiledOperation,
        artifacts_store: V1Connection,
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        default_sa: Optional[str] = None,
        default_auth: bool = False,
    ) -> Resource:
        raise NotImplementedError
