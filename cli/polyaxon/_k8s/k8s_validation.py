from typing import Dict, Optional, Type, TypeVar, Union

from clipped.utils.strings import to_snake_case

from polyaxon._k8s import k8s_schemas

Swagger = TypeVar("Swagger")


def _validate_schema(value: Optional[Union[Swagger, Dict]], cls: Type[Swagger]):
    if value is None:
        return value
    if isinstance(value, dict):
        return cls(**{to_snake_case(k): value[k] for k in value})
    if isinstance(value, cls):
        return value
    raise TypeError(
        "This field expects a dict or an instance of {}.".format(cls.__name__)
    )


def validate_k8s_affinity(value: Optional[Union[k8s_schemas.V1Affinity, Dict]]):
    return _validate_schema(value, k8s_schemas.V1Affinity)


def validate_k8s_security_context(
    value: Optional[Union[k8s_schemas.V1SecurityContext, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1SecurityContext)


def validate_k8s_pod_dns_config(
    value: Optional[Union[k8s_schemas.V1PodDNSConfig, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1PodDNSConfig)


def validate_k8s_toleration(value: Optional[Union[k8s_schemas.V1Toleration, Dict]]):
    return _validate_schema(value, k8s_schemas.V1Toleration)


def validate_k8s_host_alias(value: Optional[Union[k8s_schemas.V1HostAlias, Dict]]):
    return _validate_schema(value, k8s_schemas.V1HostAlias)


def validate_k8s_container(value: Optional[Union[k8s_schemas.V1Container, Dict]]):
    return _validate_schema(value, k8s_schemas.V1Container)


def validate_k8s_env_var(value: Optional[Union[k8s_schemas.V1EnvVar, Dict]]):
    return _validate_schema(value, k8s_schemas.V1EnvVar)


def validate_k8s_volume_mount(value: Optional[Union[k8s_schemas.V1VolumeMount, Dict]]):
    return _validate_schema(value, k8s_schemas.V1VolumeMount)


def validate_k8s_container_port(
    value: Optional[Union[k8s_schemas.V1ContainerPort, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1ContainerPort)


def validate_k8s_resource_requirements(
    value: Optional[Union[k8s_schemas.V1ResourceRequirements, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1ResourceRequirements)


def validate_k8s_env_from_source(
    value: Optional[Union[k8s_schemas.V1EnvFromSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1EnvFromSource)


def validate_k8s_volume(value: Optional[Union[k8s_schemas.V1Volume, Dict]]):
    return _validate_schema(value, k8s_schemas.V1Volume)


def validate_k8s_object_field_selector(
    value: Optional[Union[k8s_schemas.V1ObjectFieldSelector, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1ObjectFieldSelector)


def validate_k8s_env_var_source(
    value: Optional[Union[k8s_schemas.V1EnvVarSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1EnvVarSource)


def validate_k8s_config_map_selector(
    value: Optional[Union[k8s_schemas.V1ConfigMapKeySelector, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1ConfigMapKeySelector)


def validate_k8s_secret_selector(
    value: Optional[Union[k8s_schemas.V1SecretKeySelector, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1SecretKeySelector)


def validate_k8s_pod_spec(value: Optional[Union[k8s_schemas.V1PodSpec, Dict]]):
    return _validate_schema(value, k8s_schemas.V1PodSpec)


def validate_k8s_object_meta(value: Optional[Union[k8s_schemas.V1ObjectMeta, Dict]]):
    return _validate_schema(value, k8s_schemas.V1ObjectMeta)


def validate_k8s_pod_template_spec(
    value: Optional[Union[k8s_schemas.V1PodTemplateSpec, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1PodTemplateSpec)


def validate_k8s_host_path_volume_source(
    value: Optional[Union[k8s_schemas.V1HostPathVolumeSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1HostPathVolumeSource)


def validate_k8s_empty_dir_volume_source(
    value: Optional[Union[k8s_schemas.V1EmptyDirVolumeSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1EmptyDirVolumeSource)


def validate_k8s_persistent_volume_claim_volume_source(
    value: Optional[Union[k8s_schemas.V1PersistentVolumeClaimVolumeSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1PersistentVolumeClaimVolumeSource)


def validate_k8s_secret_volume_source(
    value: Optional[Union[k8s_schemas.V1SecretVolumeSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1SecretVolumeSource)


def validate_k8s_config_map_volume_source(
    value: Optional[Union[k8s_schemas.V1ConfigMapVolumeSource, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1ConfigMapVolumeSource)


def validate_k8s_local_object_reference(
    value: Optional[Union[k8s_schemas.V1LocalObjectReference, Dict]]
):
    return _validate_schema(value, k8s_schemas.V1LocalObjectReference)
