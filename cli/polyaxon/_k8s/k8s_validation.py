from typing import Any, Dict, Optional, Type, TypeVar, Union

from clipped.utils.strings import to_snake_case
from polyaxon._k8s import k8s_schemas
from polyaxon._vendor.k8s import models


Swagger = TypeVar("Swagger")

VENDORED_MODELS = {
    name: cls for name, cls in vars(models).items() if isinstance(cls, type)
}


def _to_vendored(value: Any) -> Any:
    """Converts `kubernetes` client models nested in `value` to the vendored models.

    Returns `value` itself when it holds no client models.
    """
    if isinstance(value, list):
        converted = [_to_vendored(v) for v in value]
        return value if all(c is v for c, v in zip(converted, value)) else converted
    if isinstance(value, dict):
        converted = {k: _to_vendored(v) for k, v in value.items()}
        return value if all(converted[k] is v for k, v in value.items()) else converted

    cls = VENDORED_MODELS.get(type(value).__name__)
    if cls is None:
        return value
    if isinstance(value, cls):
        for attr in cls.openapi_types:
            current = getattr(value, attr)
            converted = _to_vendored(current)
            if converted is not current:
                setattr(value, attr, converted)
        return value
    if not type(value).__module__.startswith("kubernetes"):
        return value

    unsupported = [
        attr
        for attr in type(value).openapi_types
        if attr not in cls.openapi_types and getattr(value, attr, None) is not None
    ]
    if unsupported:
        raise ValueError(
            "{} fields {} are not supported.".format(cls.__name__, unsupported)
        )
    kwargs = {
        attr: _to_vendored(getattr(value, attr, None)) for attr in cls.openapi_types
    }
    configuration = getattr(value, "local_vars_configuration", None)
    if configuration is not None:
        kwargs["local_vars_configuration"] = configuration
    return cls(**kwargs)


def _validate_schema(value: Optional[Union[Swagger, Dict]], cls: Type[Swagger]):
    if value is None:
        return value
    if isinstance(value, dict):
        return cls(**{to_snake_case(k): _to_vendored(value[k]) for k in value})
    value = _to_vendored(value)
    if isinstance(value, cls):
        return value
    raise ValueError(
        "This field expects a dict or an instance of {}.".format(cls.__name__)
    )


def validate_k8s_affinity(value: Optional[Union[k8s_schemas.V1Affinity, Dict]]):
    return _validate_schema(value, k8s_schemas.V1Affinity)


def validate_k8s_security_context(
    value: Optional[Union[k8s_schemas.V1SecurityContext, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1SecurityContext)


def validate_k8s_pod_dns_config(
    value: Optional[Union[k8s_schemas.V1PodDNSConfig, Dict]],
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
    value: Optional[Union[k8s_schemas.V1ContainerPort, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1ContainerPort)


def validate_k8s_resource_requirements(
    value: Optional[Union[k8s_schemas.V1ResourceRequirements, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1ResourceRequirements)


def validate_k8s_env_from_source(
    value: Optional[Union[k8s_schemas.V1EnvFromSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1EnvFromSource)


def validate_k8s_volume(value: Optional[Union[k8s_schemas.V1Volume, Dict]]):
    return _validate_schema(value, k8s_schemas.V1Volume)


def validate_k8s_object_field_selector(
    value: Optional[Union[k8s_schemas.V1ObjectFieldSelector, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1ObjectFieldSelector)


def validate_k8s_env_var_source(
    value: Optional[Union[k8s_schemas.V1EnvVarSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1EnvVarSource)


def validate_k8s_config_map_selector(
    value: Optional[Union[k8s_schemas.V1ConfigMapKeySelector, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1ConfigMapKeySelector)


def validate_k8s_secret_selector(
    value: Optional[Union[k8s_schemas.V1SecretKeySelector, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1SecretKeySelector)


def validate_k8s_pod_spec(value: Optional[Union[k8s_schemas.V1PodSpec, Dict]]):
    return _validate_schema(value, k8s_schemas.V1PodSpec)


def validate_k8s_object_meta(value: Optional[Union[k8s_schemas.V1ObjectMeta, Dict]]):
    return _validate_schema(value, k8s_schemas.V1ObjectMeta)


def validate_k8s_pod_template_spec(
    value: Optional[Union[k8s_schemas.V1PodTemplateSpec, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1PodTemplateSpec)


def validate_k8s_host_path_volume_source(
    value: Optional[Union[k8s_schemas.V1HostPathVolumeSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1HostPathVolumeSource)


def validate_k8s_empty_dir_volume_source(
    value: Optional[Union[k8s_schemas.V1EmptyDirVolumeSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1EmptyDirVolumeSource)


def validate_k8s_persistent_volume_claim_volume_source(
    value: Optional[Union[k8s_schemas.V1PersistentVolumeClaimVolumeSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1PersistentVolumeClaimVolumeSource)


def validate_k8s_secret_volume_source(
    value: Optional[Union[k8s_schemas.V1SecretVolumeSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1SecretVolumeSource)


def validate_k8s_config_map_volume_source(
    value: Optional[Union[k8s_schemas.V1ConfigMapVolumeSource, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1ConfigMapVolumeSource)


def validate_k8s_local_object_reference(
    value: Optional[Union[k8s_schemas.V1LocalObjectReference, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1LocalObjectReference)


def validate_k8s_pod_failure_policy(
    value: Optional[Union[k8s_schemas.V1PodFailurePolicy, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1PodFailurePolicy)


def validate_k8s_exec_action(
    value: Optional[Union[k8s_schemas.V1ExecAction, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1ExecAction)


def validate_k8s_http_get_action(
    value: Optional[Union[k8s_schemas.V1HTTPGetAction, Dict]],
):
    return _validate_schema(value, k8s_schemas.V1HTTPGetAction)
