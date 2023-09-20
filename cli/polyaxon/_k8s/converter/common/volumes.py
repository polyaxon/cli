from typing import Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._contexts import paths as ctx_paths
from polyaxon._k8s import k8s_schemas
from polyaxon._runner.converter.common import constants


def get_volume_from_connection(
    connection: V1Connection,
) -> Optional[k8s_schemas.V1Volume]:
    if not connection:
        return None
    if connection.is_volume_claim:
        pv_claim = k8s_schemas.V1PersistentVolumeClaimVolumeSource(
            claim_name=connection.schema_.volume_claim,
            read_only=connection.schema_.read_only,
        )
        return k8s_schemas.V1Volume(
            name=connection.name, persistent_volume_claim=pv_claim
        )

    if connection.is_host_path:
        return k8s_schemas.V1Volume(
            name=connection.name,
            host_path=k8s_schemas.V1HostPathVolumeSource(
                path=connection.schema_.host_path
            ),
        )


def get_volume_from_secret(
    secret: V1ConnectionResource,
) -> Optional[k8s_schemas.V1Volume]:
    if not secret:
        return None
    if secret.mount_path:
        secret_volume = k8s_schemas.V1SecretVolumeSource(
            secret_name=secret.name,
            items=secret.items,
            default_mode=secret.default_mode,
        )
        return k8s_schemas.V1Volume(name=secret.name, secret=secret_volume)


def get_volume_from_config_map(
    config_map: V1ConnectionResource,
) -> Optional[k8s_schemas.V1Volume]:
    if not config_map:
        return None
    if config_map.mount_path:
        config_map_volume = k8s_schemas.V1ConfigMapVolumeSource(
            name=config_map.name,
            items=config_map.items,
            default_mode=config_map.default_mode,
        )
        return k8s_schemas.V1Volume(name=config_map.name, config_map=config_map_volume)


def get_volume(
    volume: str,
    claim_name: Optional[str] = None,
    host_path: Optional[str] = None,
    read_only: Optional[bool] = None,
) -> k8s_schemas.V1Volume:
    if claim_name:
        pv_claim = k8s_schemas.V1PersistentVolumeClaimVolumeSource(
            claim_name=claim_name, read_only=read_only
        )
        return k8s_schemas.V1Volume(name=volume, persistent_volume_claim=pv_claim)

    if host_path:
        return k8s_schemas.V1Volume(
            name=volume, host_path=k8s_schemas.V1HostPathVolumeSource(path=host_path)
        )

    empty_dir = k8s_schemas.V1EmptyDirVolumeSource()
    return k8s_schemas.V1Volume(name=volume, empty_dir=empty_dir)


def get_docker_context_volume() -> k8s_schemas.V1Volume:
    return get_volume(
        volume=constants.VOLUME_MOUNT_DOCKER, host_path=ctx_paths.CONTEXT_MOUNT_DOCKER
    )


def get_configs_context_volume() -> k8s_schemas.V1Volume:
    return get_volume(volume=constants.VOLUME_MOUNT_CONFIGS)


def get_artifacts_context_volume() -> k8s_schemas.V1Volume:
    return get_volume(volume=constants.VOLUME_MOUNT_ARTIFACTS)


def get_connections_context_volume(name: str) -> k8s_schemas.V1Volume:
    return get_volume(volume=name)


def get_shm_context_volume() -> k8s_schemas.V1Volume:
    """
    Mount an tmpfs volume to /dev/shm.
    This will set /dev/shm size to half of the RAM of node.
    By default, /dev/shm is very small, only 64MB.
    Some experiments will fail due to lack of share memory,
    such as some experiments running on Pytorch.
    """
    return k8s_schemas.V1Volume(
        name=constants.VOLUME_MOUNT_SHM,
        empty_dir=k8s_schemas.V1EmptyDirVolumeSource(medium="Memory"),
    )
