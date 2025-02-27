from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
    validation_after,
    validation_always,
    validation_before,
)
from clipped.formatting import Printer

from polyaxon._auxiliaries import (
    V1PolyaxonCleaner,
    V1PolyaxonInitContainer,
    V1PolyaxonNotifier,
    V1PolyaxonSidecarContainer,
)
from polyaxon._auxiliaries.default_scheduling import V1DefaultScheduling
from polyaxon._connections import V1Connection
from polyaxon._deploy.schemas.auth import AuthConfig
from polyaxon._deploy.schemas.deployment_types import DeploymentCharts, DeploymentTypes
from polyaxon._deploy.schemas.email import EmailConfig
from polyaxon._deploy.schemas.ingress import IngressConfig
from polyaxon._deploy.schemas.intervals import IntervalsConfig
from polyaxon._deploy.schemas.operators import OperatorsConfig
from polyaxon._deploy.schemas.proxy import ProxyConfig
from polyaxon._deploy.schemas.rbac import RBACConfig
from polyaxon._deploy.schemas.root_user import RootUserConfig
from polyaxon._deploy.schemas.security_context import SecurityContextConfig
from polyaxon._deploy.schemas.service import (
    AgentServiceConfig,
    ApiServiceConfig,
    DeploymentService,
    ExternalServicesConfig,
    HooksConfig,
    OperatorServiceConfig,
    PostgresqlConfig,
    RabbitmqConfig,
    RedisConfig,
    WorkerServiceConfig,
)
from polyaxon._deploy.schemas.ssl import SSLConfig
from polyaxon._deploy.schemas.ui import UIConfig
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel


def validate_connections(artifacts_store, connections):
    connections = connections or []

    connection_names = set()

    if artifacts_store:
        connection_names.add(artifacts_store.name)

    for c in connections:
        if c.name in connection_names:
            raise ValueError(
                "A connection with name `{}` must be unique.".format(c.name)
            )
        connection_names.add(c.name)


def check_postgres(postgresql, external_services):
    postgresql_disabled = postgresql.enabled is False if postgresql else False
    external_postgresql = None
    if external_services:
        external_postgresql = external_services.postgresql

    if postgresql_disabled and not external_postgresql:
        raise ValueError(
            "A postgresql instance is required, "
            "please enable the in-cluster postgresql, "
            "or provide an external instance."
        )


def check_rabbitmq(rabbitmq, external_services, broker):
    rabbitmq_enabled = rabbitmq and rabbitmq.enabled
    external_rabbitmq = None
    rabbitmq_broker = broker != "redis"
    if external_services:
        external_rabbitmq = external_services.rabbitmq

    if rabbitmq_enabled and external_rabbitmq:
        raise ValueError(
            "You can either enable the in-cluster rabbitmq or use an external instance, "
            "not both!"
        )
    rabbitmq_used = rabbitmq_enabled or external_rabbitmq
    if rabbitmq_used and not rabbitmq_broker:
        raise ValueError(
            "rabbitmq is enabled but you are using a different broker backend!"
        )

    return rabbitmq_used


def check_redis(redis, external_services, broker):
    redis_enabled = redis and redis.enabled
    redis_non_broker = redis and redis.non_broker
    external_redis = None
    redis_broker = broker == "redis"
    if external_services:
        external_redis = external_services.redis

    if redis_enabled and external_redis:
        raise ValueError(
            "You can either enable the in-cluster redis or use an external instance, "
            "not both!"
        )

    redis_used = redis_enabled or external_redis
    if redis_used and not redis_broker and not redis_non_broker:
        raise ValueError(
            "redis is enabled but you are using a different broker backend!"
        )

    return redis_used, not redis_non_broker


def broker_is_required(services):
    for s in services:
        if s and s.enabled:
            return True
    return False


def wrong_agent_deployment_keys(**kwargs):
    error_keys = []
    for k, v in kwargs.items():
        if v is not None:
            error_keys.append(k)
    if error_keys:
        raise ValueError(
            "Agent deployment received some keys that are not required.\n"
            "Please remove these config keys from your config file:\n"
            "{}".format(error_keys)
        )


def validate_platform_deployment(
    postgresql,
    redis,
    rabbitmq,
    broker,
    scheduler,
    compiler,
    worker,
    beat,
    external_services,
):
    check_postgres(postgresql, external_services)
    redis_used, redis_is_broker = check_redis(redis, external_services, broker)
    rabbitmq_used = check_rabbitmq(rabbitmq, external_services, broker)
    if rabbitmq_used and redis_used and redis_is_broker:
        raise ValueError(
            "You only need to enable rabbitmq or redis for the broker, "
            "you don't need to deploy both!"
        )
    broker_defined = rabbitmq_used or redis_used
    services = [scheduler, compiler, worker, beat]
    if broker_is_required(services) and not broker_defined:
        raise ValueError(
            "You enabled some services that require a broker, please set redis or rabbitmq!"
        )


def validate_deployment_chart(
    deployment_chart,
    agent,
    environment,
):
    if deployment_chart == DeploymentCharts.AGENT and not agent:
        raise ValueError("Agent deployment requires a valid `agent` key configuration.")

    if deployment_chart == DeploymentCharts.PLATFORM and agent and agent.enabled:
        Printer.header("Deployment has agent enabled!")


class DeploymentConfig(BaseSchemaModel):
    _SWAGGER_FIELDS_LISTS = ["tolerations", "celeryTolerations"]
    _SWAGGER_FIELDS = [
        "tolerations",
        "affinity",
        "celeryTolerations",
        "celeryAffinity",
    ]

    deployment_type: Optional[DeploymentTypes] = Field(
        alias="deploymentType", default=None
    )
    deployment_chart: Optional[DeploymentCharts] = Field(
        default=DeploymentCharts.PLATFORM, alias="deploymentChart"
    )
    deployment_version: Optional[StrictStr] = Field(
        alias="deploymentVersion", default=None
    )
    release_name: Optional[StrictStr] = Field(alias="releaseName", default=None)
    namespace: Optional[StrictStr] = Field(default=None)
    rbac: Optional[RBACConfig] = None
    polyaxon_secret: Optional[StrictStr] = Field(alias="polyaxonSecret", default=None)
    internal_token: Optional[StrictStr] = Field(alias="internalToken", default=None)
    password_length: Optional[StrictInt] = Field(alias="passwordLength", default=None)
    password_auth: Optional[bool] = Field(alias="passwordAuth", default=None)
    ssl: Optional[SSLConfig] = None
    encryption_secret: Optional[StrictStr] = Field(
        alias="encryptionSecret", default=None
    )
    platform_secret: Optional[StrictStr] = Field(alias="platformSecret", default=None)
    agent_secret: Optional[StrictStr] = Field(alias="agentSecret", default=None)
    timezone: Optional[StrictStr] = Field(default=None)
    environment: Optional[StrictStr] = Field(default=None)
    ingress: Optional[IngressConfig] = None
    user: Optional[RootUserConfig] = None
    node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(
        alias="nodeSelector", default=None
    )
    tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]] = None
    affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]] = None
    labels: Optional[Dict[StrictStr, StrictStr]] = Field(alias="labels", default=None)
    annotations: Optional[Dict[StrictStr, StrictStr]] = Field(
        alias="annotations", default=None
    )
    priority_class_name: Optional[StrictStr] = Field(
        alias="priorityClassName", default=None
    )
    celery_node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(
        alias="celeryNodeSelector", default=None
    )
    celery_tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]] = Field(
        alias="celeryTolerations", default=None
    )
    celery_affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]] = Field(
        alias="celeryAffinity", default=None
    )
    limit_resources: Optional[bool] = Field(alias="limitResources", default=None)
    global_replicas: Optional[StrictInt] = Field(alias="globalReplicas", default=None)
    global_concurrency: Optional[StrictInt] = Field(
        alias="globalConcurrency", default=None
    )
    gateway: Optional[ApiServiceConfig] = None
    scheduler: Optional[WorkerServiceConfig] = None
    compiler: Optional[WorkerServiceConfig] = None
    worker: Optional[WorkerServiceConfig] = None
    beat: Optional[DeploymentService] = None
    agent: Optional[AgentServiceConfig] = None
    operator: Optional[OperatorServiceConfig] = None
    init: Optional[V1PolyaxonInitContainer] = None
    sidecar: Optional[V1PolyaxonSidecarContainer] = None
    notifier: Optional[V1PolyaxonNotifier] = None
    cleaner: Optional[V1PolyaxonCleaner] = None
    default_scheduling: Optional[V1DefaultScheduling] = Field(
        alias="defaultScheduling", default=None
    )
    default_image_pull_secrets: Optional[List[StrictStr]] = Field(
        alias="defaultImagePullSecrets", default=None
    )
    clean_hooks: Optional[HooksConfig] = Field(alias="cleanHooks", default=None)
    api_hooks: Optional[HooksConfig] = Field(alias="apiHooks", default=None)
    flower: Optional[DeploymentService] = None
    postgresql: Optional[PostgresqlConfig] = None
    redis: Optional[RedisConfig] = None
    rabbitmq: Optional[RabbitmqConfig] = None
    broker: Optional[Literal["redis", "rabbitmq"]] = None
    email: Optional[EmailConfig] = None
    ldap: Optional[Dict] = None
    metrics: Optional[Dict] = None
    image_pull_secrets: Optional[List[StrictStr]] = Field(
        alias="imagePullSecrets", default=None
    )
    host_name: Optional[StrictStr] = Field(alias="hostName", default=None)
    allowed_hosts: Optional[List[StrictStr]] = Field(alias="allowedHosts", default=None)
    include_host_ips: Optional[bool] = Field(alias="includeHostIps", default=None)
    intervals: Optional[IntervalsConfig] = None
    cleaning_intervals: Optional[Dict] = Field(alias="cleaningIntervals", default=None)
    artifacts_store: Optional[V1Connection] = Field(
        alias="artifactsStore", default=None
    )
    connections: Optional[List[V1Connection]] = Field(default=None)
    mount_connections: Optional[List[str]] = Field(
        alias="mountConnections", default=None
    )
    log_level: Optional[StrictStr] = Field(alias="logLevel", default=None)
    security_context: Optional[SecurityContextConfig] = Field(
        alias="securityContext", default=None
    )
    external_services: Optional[ExternalServicesConfig] = Field(
        alias="externalServices", default=None
    )
    debug_mode: Optional[bool] = Field(alias="debugMode", default=None)
    organization_key: Optional[StrictStr] = Field(alias="organizationKey", default=None)
    auth: Optional[AuthConfig] = None
    proxy: Optional[ProxyConfig] = None
    ui: Optional[UIConfig] = None
    include_chart_revision: Optional[bool] = Field(
        alias="includeChartRevision", default=None
    )
    operators: Optional[OperatorsConfig] = None
    istio: Optional[Dict] = None
    dns: Optional[Dict] = None

    @model_validator(**validation_after)
    def validate_deployment(cls, values):
        validate_deployment_chart(
            deployment_chart=cls.get_value_for_key("deployment_chart", values),
            agent=cls.get_value_for_key("agent", values),
            environment=cls.get_value_for_key("environment", values),
        )
        validate_platform_deployment(
            postgresql=cls.get_value_for_key("postgresql", values),
            redis=cls.get_value_for_key("redis", values),
            rabbitmq=cls.get_value_for_key("rabbitmq", values),
            broker=cls.get_value_for_key("broker", values),
            scheduler=cls.get_value_for_key("scheduler", values),
            compiler=cls.get_value_for_key("compiler", values),
            worker=cls.get_value_for_key("worker", values),
            beat=cls.get_value_for_key("beat", values),
            external_services=cls.get_value_for_key("external_services", values),
        )
        if cls.get_value_for_key("deployment_chart", values) == DeploymentCharts.AGENT:
            wrong_agent_deployment_keys(
                password_length=cls.get_value_for_key("password_length", values),
                password_auth=cls.get_value_for_key("password_auth", values),
                platform_secret=cls.get_value_for_key("platform_secret", values),
                encryption_secret=cls.get_value_for_key("encryption_secret", values),
                user=cls.get_value_for_key("user", values),
                global_replicas=cls.get_value_for_key("global_replicas", values),
                global_concurrency=cls.get_value_for_key("global_concurrency", values),
                scheduler=cls.get_value_for_key("scheduler", values),
                compiler=cls.get_value_for_key("compiler", values),
                worker=cls.get_value_for_key("worker", values),
                beat=cls.get_value_for_key("beat", values),
                clean_hook=cls.get_value_for_key("clean_hook", values),
                api_hooks=cls.get_value_for_key("api_hooks", values),
                flower=cls.get_value_for_key("flower", values),
                postgresql=cls.get_value_for_key("postgresql", values),
                redis=cls.get_value_for_key("redis", values),
                rabbitmq=cls.get_value_for_key("rabbitmq", values),
                broker=cls.get_value_for_key("broker", values),
                email=cls.get_value_for_key("email", values),
                ldap=cls.get_value_for_key("ldap", values),
                intervals=cls.get_value_for_key("intervals", values),
                metrics=cls.get_value_for_key("metrics", values),
                organization_key=cls.get_value_for_key("organization_key", values),
            )

        return values

    @field_validator(
        "affinity", "celery_affinity", **validation_always, **validation_before
    )
    def validate_affinity(cls, v):
        return k8s_validation.validate_k8s_affinity(v)

    @field_validator(
        "tolerations", "celery_tolerations", **validation_always, **validation_before
    )
    def validate_tolerations(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_toleration(vi) for vi in v]
