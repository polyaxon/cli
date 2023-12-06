from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    StrictInt,
    StrictStr,
    root_validator,
    validator,
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
    _SWAGGER_FIELDS = [
        "tolerations",
        "affinity",
        "celeryTolerations",
        "celeryAffinity",
    ]

    deployment_type: Optional[DeploymentTypes] = Field(alias="deploymentType")
    deployment_chart: Optional[DeploymentCharts] = Field(
        default=DeploymentCharts.PLATFORM, alias="deploymentChart"
    )
    deployment_version: Optional[StrictStr] = Field(alias="deploymentVersion")
    release_name: Optional[StrictStr] = Field(alias="releaseName")
    namespace: Optional[StrictStr]
    rbac: Optional[RBACConfig]
    polyaxon_secret: Optional[StrictStr] = Field(alias="polyaxonSecret")
    internal_token: Optional[StrictStr] = Field(alias="internalToken")
    password_length: Optional[StrictInt] = Field(alias="passwordLength")
    password_auth: Optional[bool] = Field(alias="passwordAuth")
    ssl: Optional[SSLConfig]
    encryption_secret: Optional[StrictStr] = Field(alias="encryptionSecret")
    platform_secret: Optional[StrictStr] = Field(alias="platformSecret")
    agent_secret: Optional[StrictStr] = Field(alias="agentSecret")
    timezone: Optional[StrictStr]
    environment: Optional[StrictStr]
    ingress: Optional[IngressConfig]
    user: Optional[RootUserConfig]
    node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(alias="nodeSelector")
    tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]]
    affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]]
    labels: Optional[Dict[StrictStr, StrictStr]] = Field(alias="labels")
    annotations: Optional[Dict[StrictStr, StrictStr]] = Field(alias="annotations")
    priority_class_name: Optional[StrictStr] = Field(alias="priorityClassName")
    celery_node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(
        alias="celeryNodeSelector"
    )
    celery_tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]] = Field(
        alias="celeryTolerations"
    )
    celery_affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]] = Field(
        alias="celeryAffinity"
    )
    limit_resources: Optional[bool] = Field(alias="limitResources")
    global_replicas: Optional[StrictInt] = Field(alias="globalReplicas")
    global_concurrency: Optional[StrictInt] = Field(alias="globalConcurrency")
    gateway: Optional[ApiServiceConfig]
    scheduler: Optional[WorkerServiceConfig]
    compiler: Optional[WorkerServiceConfig]
    worker: Optional[WorkerServiceConfig]
    beat: Optional[DeploymentService]
    agent: Optional[AgentServiceConfig]
    operator: Optional[OperatorServiceConfig]
    init: Optional[V1PolyaxonInitContainer]
    sidecar: Optional[V1PolyaxonSidecarContainer]
    notifier: Optional[V1PolyaxonNotifier]
    cleaner: Optional[V1PolyaxonCleaner]
    default_scheduling: Optional[V1DefaultScheduling] = Field(alias="defaultScheduling")
    default_image_pull_secrets: Optional[List[StrictStr]] = Field(
        alias="defaultImagePullSecrets"
    )
    clean_hooks: Optional[HooksConfig] = Field(alias="cleanHooks")
    api_hooks: Optional[HooksConfig] = Field(alias="apiHooks")
    flower: Optional[DeploymentService]
    postgresql: Optional[PostgresqlConfig]
    redis: Optional[RedisConfig]
    rabbitmq: Optional[RabbitmqConfig]
    broker: Optional[Literal["redis", "rabbitmq"]]
    email: Optional[EmailConfig]
    ldap: Optional[Dict]
    metrics: Optional[Dict]
    image_pull_secrets: Optional[List[StrictStr]] = Field(alias="imagePullSecrets")
    host_name: Optional[StrictStr] = Field(alias="hostName")
    allowed_hosts: Optional[List[StrictStr]] = Field(alias="allowedHosts")
    include_host_ips: Optional[bool] = Field(alias="includeHostIps")
    intervals: Optional[IntervalsConfig]
    artifacts_store: Optional[V1Connection] = Field(alias="artifactsStore")
    connections: Optional[List[V1Connection]]
    mount_connections: Optional[List[str]] = Field(alias="mountConnections")
    log_level: Optional[StrictStr] = Field(alias="logLevel")
    security_context: Optional[SecurityContextConfig] = Field(alias="securityContext")
    external_services: Optional[ExternalServicesConfig] = Field(
        alias="externalServices"
    )
    debug_mode: Optional[bool] = Field(alias="debugMode")
    organization_key: Optional[StrictStr] = Field(alias="organizationKey")
    auth: Optional[AuthConfig]
    proxy: Optional[ProxyConfig]
    ui: Optional[UIConfig]
    include_chart_revision: Optional[bool] = Field(alias="includeChartRevision")
    operators: Optional[OperatorsConfig]
    istio: Optional[Dict]
    dns: Optional[Dict]

    @root_validator
    def validate_deployment(cls, values):
        validate_deployment_chart(
            deployment_chart=values.get("deployment_chart"),
            agent=values.get("agent"),
            environment=values.get("environment"),
        )
        validate_platform_deployment(
            postgresql=values.get("postgresql"),
            redis=values.get("redis"),
            rabbitmq=values.get("rabbitmq"),
            broker=values.get("broker"),
            scheduler=values.get("scheduler"),
            compiler=values.get("compiler"),
            worker=values.get("worker"),
            beat=values.get("beat"),
            external_services=values.get("external_services"),
        )
        if values.get("deployment_chart") == DeploymentCharts.AGENT:
            wrong_agent_deployment_keys(
                password_length=values.get("password_length"),
                password_auth=values.get("password_auth"),
                platform_secret=values.get("platform_secret"),
                encryption_secret=values.get("encryption_secret"),
                user=values.get("user"),
                global_replicas=values.get("global_replicas"),
                global_concurrency=values.get("global_concurrency"),
                scheduler=values.get("scheduler"),
                compiler=values.get("compiler"),
                worker=values.get("worker"),
                beat=values.get("beat"),
                clean_hook=values.get("clean_hook"),
                api_hooks=values.get("api_hooks"),
                flower=values.get("flower"),
                postgresql=values.get("postgresql"),
                redis=values.get("redis"),
                rabbitmq=values.get("rabbitmq"),
                broker=values.get("broker"),
                email=values.get("email"),
                ldap=values.get("ldap"),
                intervals=values.get("intervals"),
                metrics=values.get("metrics"),
                organization_key=values.get("organization_key"),
                ui=values.get("ui"),
            )

        return values

    @validator("affinity", "celery_affinity", always=True, pre=True)
    def validate_affinity(cls, v):
        return k8s_validation.validate_k8s_affinity(v)

    @validator("tolerations", "celery_tolerations", always=True, pre=True)
    def validate_tolerations(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_toleration(vi) for vi in v]
