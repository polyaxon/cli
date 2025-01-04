from typing import Any, List, Optional, Tuple, Union

from clipped.utils.enums import get_enum_value
from clipped.utils.lists import to_list

from polyaxon._auxiliaries import V1PolyaxonInitContainer
from polyaxon._connections import V1Connection, V1ConnectionKind
from polyaxon._constants.globals import DEFAULT
from polyaxon._containers.names import (
    INIT_ARTIFACTS_CONTAINER_PREFIX,
    INIT_AUTH_CONTAINER,
    INIT_CUSTOM_CONTAINER_PREFIX,
    INIT_DOCKERFILE_CONTAINER_PREFIX,
    INIT_FILE_CONTAINER_PREFIX,
    INIT_GIT_CONTAINER_PREFIX,
    INIT_TENSORBOARD_CONTAINER_PREFIX,
    generate_container_name,
)
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_SSH_PATH
from polyaxon._flow import V1Plugins
from polyaxon._local_process import process_types
from polyaxon._runner.converter import BaseConverter as _BaseConverter
from polyaxon._runner.converter.init.artifacts import init_artifact_context_args
from polyaxon._runner.converter.init.file import FILE_INIT_COMMAND, get_file_init_args
from polyaxon._runner.converter.init.git import REPO_INIT_COMMAND, get_repo_context_args
from polyaxon._runner.converter.init.store import get_volume_args
from polyaxon._runner.converter.init.tensorboard import (
    TENSORBOARD_INIT_COMMAND,
    get_tensorboard_args,
)
from polyaxon._schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1TensorboardType,
)
from polyaxon.exceptions import PolyaxonConverterError


class InitConverter(_BaseConverter):
    @classmethod
    def _get_base_store_container(
        cls,
        container: Optional[process_types.V1Container],
        container_name: str,
        polyaxon_init: V1PolyaxonInitContainer,
        store: V1Connection,
        env: List[process_types.V1EnvVar],
        env_from: List[Any],
        args: List[str],
        command: Optional[List[str]] = None,
        **kwargs,
    ) -> Optional[process_types.V1Container]:
        env = env or []

        # Artifact store needs to allow init the contexts as well, so the store is not required
        if not store:
            raise PolyaxonConverterError("Init store container requires a store")

        if store.is_bucket:
            secret = store.secret
            env = env + to_list(
                cls._get_items_from_json_resource(resource=secret), check_none=True
            )
            config_map = store.config_map
            env = env + to_list(
                cls._get_from_json_resource(resource=config_map),
                check_none=True,
            )
        # Add connections catalog env vars information
        connection_env = cls._get_connections_catalog_env_var(connections=[store])
        if connection_env:
            env.append(connection_env)

        return cls._patch_container(
            container=container,
            name=container_name,
            command=command or ["/bin/sh", "-c"],
            args=args,
            env=env,
        )

    @classmethod
    def _get_custom_init_container(
        cls,
        connection: V1Connection,
        plugins: V1Plugins,
        container: Optional[process_types.V1Container],
        run_path: str,
        env: List[process_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> process_types.V1Container:
        if not connection:
            raise PolyaxonConverterError(
                "A connection is required to create a repo context."
            )

        env = to_list(env, check_none=True)
        secret = connection.secret
        if secret:
            env += to_list(
                cls._get_from_json_resource(resource=secret), check_none=True
            )

        # Add connections catalog env vars information
        connection_env = cls._get_connections_catalog_env_var(connections=[connection])
        if connection_env:
            env.append(connection_env)
        connection_env = cls._get_connection_env_var(connection=connection)
        if connection_env:
            env.append(connection_env)
        config_map = connection.config_map
        if config_map:
            env += to_list(
                cls._get_from_json_resource(resource=config_map),
                check_none=True,
            )
        container_name = container.name or generate_container_name(
            INIT_CUSTOM_CONTAINER_PREFIX, connection.name
        )
        return cls._patch_container(
            container=container,
            name=container_name,
            env=env,
        )

    @classmethod
    def _get_dockerfile_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        dockerfile_args: V1DockerfileType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[process_types.V1Container] = None,
        env: List[process_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> process_types.V1Container:
        env = to_list(env, check_none=True)
        env = env + [cls._get_run_instance_env_var(run_instance)]

        container_name = generate_container_name(INIT_DOCKERFILE_CONTAINER_PREFIX)
        if not container:
            container = cls._new_container(name=container_name)

        mount_path = mount_path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS

        return cls._patch_container(
            container=container,
            name=container_name,
            image=polyaxon_init.get_image(),
            image_pull_policy=polyaxon_init.image_pull_policy,
            command=["polyaxon", "docker", "generate"],
            args=[
                "--build-context={}".format(dockerfile_args.to_json()),
                "--destination={}".format(mount_path),
                "--copy-path={}".format(
                    ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(run_path)
                ),
                "--track",
            ],
            env=env,
        )

    @classmethod
    def _get_file_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        file_args: V1FileType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[process_types.V1Container] = None,
        env: List[process_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> process_types.V1Container:
        env = to_list(env, check_none=True)
        env = env + [cls._get_run_instance_env_var(run_instance)]

        container_name = generate_container_name(INIT_FILE_CONTAINER_PREFIX)
        if not container:
            container = cls._new_container(name=container_name)

        mount_path = mount_path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS

        file_args.filename = file_args.filename or "file"
        return cls._patch_container(
            container=container,
            name=container_name,
            image=polyaxon_init.get_image(),
            image_pull_policy=polyaxon_init.image_pull_policy,
            command=FILE_INIT_COMMAND,
            args=get_file_init_args(
                file_args=file_args, run_path=run_path, mount_path=mount_path
            ),
            env=env,
        )

    @classmethod
    def _get_git_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        plugins: V1Plugins,
        run_path: str,
        container: Optional[process_types.V1Container] = None,
        env: List[process_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        track: bool = False,
    ) -> process_types.V1Container:
        if not connection:
            raise PolyaxonConverterError(
                "A connection is required to create a repo context."
            )
        container_name = generate_container_name(
            INIT_GIT_CONTAINER_PREFIX, connection.name
        )
        if not container:
            container = cls._new_container(name=container_name)

        mount_path = mount_path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS

        env = to_list(env, check_none=True)
        env_from = []
        secret = connection.secret
        if secret:
            env += to_list(
                cls._get_from_json_resource(resource=secret), check_none=True
            )
            env_from += to_list(
                cls._get_env_from_secret(secret=secret), check_none=True
            )

        # Add connections catalog env vars information
        env += to_list(
            cls._get_connections_catalog_env_var(connections=[connection]),
            check_none=True,
        )
        env += to_list(
            cls._get_connection_env_var(connection=connection), check_none=True
        )
        # Add special handling to auto-inject ssh mount path
        if connection.kind == V1ConnectionKind.SSH and secret.mount_path:
            env += [cls._get_env_var(ENV_KEYS_SSH_PATH, secret.mount_path)]
        config_map = connection.config_map
        if config_map:
            env += to_list(
                cls._get_from_json_resource(resource=config_map),
                check_none=True,
            )
            env_from += to_list(
                cls._get_env_from_config_map(config_map=config_map),
                check_none=True,
            )
        args = get_repo_context_args(
            name=connection.name,
            # Handle the case of custom connection
            url=getattr(connection.schema_, "url", None),
            revision=getattr(connection.schema_, "revision", None),
            flags=getattr(connection.schema_, "flags", None),
            mount_path=mount_path,
            connection=connection.name if track else None,
        )
        return cls._patch_container(
            container=container,
            name=container_name,
            image=polyaxon_init.get_image(),
            image_pull_policy=polyaxon_init.image_pull_policy,
            command=REPO_INIT_COMMAND,
            args=args,
            env=env,
            env_from=env_from,
        )

    @classmethod
    def _get_store_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        connection: V1Connection,
        artifacts: V1ArtifactsType,
        paths: Union[List[str], List[Tuple[str, str]]],
        run_path: str,
        container: Optional[process_types.V1Container] = None,
        env: List[process_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
        is_default_artifacts_store: bool = False,
    ) -> process_types.V1Container:
        container_name = generate_container_name(
            INIT_ARTIFACTS_CONTAINER_PREFIX, connection.name
        )
        if not container:
            container = cls._new_container(name=container_name)

        mount_path = mount_path or (
            ctx_paths.CONTEXT_MOUNT_ARTIFACTS
            if is_default_artifacts_store
            else ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(connection.name)
        )

        return cls._get_base_store_container(
            container=container,
            container_name=container_name,
            polyaxon_init=polyaxon_init,
            store=connection,
            env=env,
            env_from=[],
            args=[
                get_volume_args(
                    store=connection,
                    mount_path=mount_path,
                    artifacts=artifacts,
                    paths=paths,
                )
            ],
        )

    @classmethod
    def _get_tensorboard_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        tb_args: V1TensorboardType,
        plugins: V1Plugins,
        run_path: str,
        run_instance: str,
        container: Optional[process_types.V1Container] = None,
        env: List[process_types.V1EnvVar] = None,
        mount_path: Optional[str] = None,
    ) -> process_types.V1Container:
        env = to_list(env, check_none=True)
        env = env + [cls._get_run_instance_env_var(run_instance)]

        container_name = generate_container_name(INIT_TENSORBOARD_CONTAINER_PREFIX)
        if not container:
            container = cls._new_container(name=container_name)

        mount_path = mount_path or ctx_paths.CONTEXT_MOUNT_ARTIFACTS

        args = get_tensorboard_args(
            tb_args=tb_args,
            context_from=artifacts_store.store_path,
            context_to=mount_path,
            connection_kind=get_enum_value(artifacts_store.kind),
        )

        return cls._get_base_store_container(
            container=container,
            container_name=container_name,
            polyaxon_init=polyaxon_init,
            store=artifacts_store,
            command=TENSORBOARD_INIT_COMMAND,
            args=args,
            env=env,
            env_from=[],
        )

    @classmethod
    def _get_auth_context_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        run_path: str,
        env: Optional[List[process_types.V1EnvVar]] = None,
    ) -> process_types.V1Container:
        env = to_list(env, check_none=True)
        container = process_types.V1Container(
            name=INIT_AUTH_CONTAINER,
            image=polyaxon_init.get_image(),
            command=["polyaxon", "initializer", "auth"],
            env=env,
        )
        return cls._patch_container(container)

    @classmethod
    def _get_artifacts_path_init_container(
        cls,
        polyaxon_init: V1PolyaxonInitContainer,
        artifacts_store: V1Connection,
        run_path: str,
        auto_resume: bool,
        env: Optional[List[process_types.V1EnvVar]] = None,
    ) -> process_types.V1Container:
        if not artifacts_store:
            raise PolyaxonConverterError("Init artifacts container requires a store.")

        env = to_list(env, check_none=True)
        init_args = init_artifact_context_args(run_path=run_path)
        if auto_resume:
            init_args.append(
                get_volume_args(
                    store=artifacts_store,
                    mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                    artifacts=V1ArtifactsType(dirs=[run_path]),
                    paths=None,
                    sync_fw=True,
                )
            )

        container_name = generate_container_name(
            INIT_ARTIFACTS_CONTAINER_PREFIX, DEFAULT, False
        )
        container = cls._new_container(name=container_name)

        return cls._get_base_store_container(
            container_name=container_name,
            container=container,
            polyaxon_init=polyaxon_init,
            store=artifacts_store,
            env=env,
            env_from=[],
            # If we are dealing with a volume we need to make sure the path exists for the user
            # We also clean the path if this is not a resume run
            args=[" ".join(init_args)],
        )
