from typing import Dict, List, Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr

from polyaxon._deploy.schemas.celery import CeleryConfig
from polyaxon._deploy.schemas.service_types import ServiceTypes
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._schemas.services import BaseServiceConfig


class DeploymentService(BaseServiceConfig):
    enabled: Optional[bool] = None
    replicas: Optional[StrictInt] = None
    concurrency: Optional[StrictInt] = None
    per_core: Optional[bool] = Field(alias="perCore", default=None)
    scheme: Optional[StrictStr] = None


class WorkerServiceConfig(DeploymentService):
    celery: Optional[CeleryConfig] = None


class AgentServiceConfig(DeploymentService):
    instance: Optional[StrictStr] = None
    token: Optional[StrictStr] = None
    watch_cluster: Optional[bool] = Field(alias="watchCluster", default=None)
    additional_namespaces: Optional[List[str]] = Field(
        alias="additionalNamespaces", default=None
    )
    service_account_annotations: Optional[Dict] = Field(
        alias="serviceAccountAnnotations", default=None
    )
    service_account_image_pull_secrets: Optional[List[StrictStr]] = Field(
        alias="serviceAccountImagePullSecrets", default=None
    )
    enable_status_finalizers: Optional[bool] = Field(
        alias="enableStatusFinalizers", default=None
    )
    enable_logs_finalizers: Optional[bool] = Field(
        alias="enableLogsFinalizers", default=None
    )
    is_replica: Optional[bool] = Field(alias="isReplica", default=None)


class OperatorServiceConfig(DeploymentService):
    skip_crd: Optional[bool] = Field(alias="skipCRD", default=None)


class BaseService(BaseSchemaModel):
    name: Optional[StrictStr] = None
    type: Optional[ServiceTypes] = None
    port: Optional[StrictInt] = None
    target_port: Optional[StrictInt] = Field(alias="targetPort", default=None)
    node_port: Optional[StrictInt] = Field(alias="nodePort", default=None)
    annotations: Optional[Dict] = None

    class Config:
        extra = "allow"


class ApiServiceConfig(DeploymentService):
    service: Optional[BaseService] = None


class HooksConfig(DeploymentService):
    load_fixtures: Optional[bool] = Field(alias="loadFixtures", default=None)
    tables: Optional[bool] = Field(alias="tables", default=None)
    sync_db: Optional[bool] = Field(alias="syncdb", default=None)
    admin_user: Optional[bool] = Field(alias="adminUser", default=None)
    default_org: Optional[bool] = Field(alias="defaultOrg", default=None)


class ThirdPartyService(DeploymentService):
    persistence: Optional[Dict] = None

    class Config:
        extra = "allow"


class PostgresqlConfig(ThirdPartyService):
    auth: Optional[Dict] = None
    conn_max_age: Optional[StrictInt] = Field(alias="connMaxAge", default=None)


class RedisConfig(ThirdPartyService):
    image: Optional[Dict] = None  # type: ignore[assignment]
    non_broker: Optional[bool] = Field(alias="nonBroker", default=None)
    use_password: Optional[bool] = Field(alias="usePassword", default=None)
    auth: Optional[Dict] = None


class RabbitmqConfig(ThirdPartyService):
    auth: Optional[Dict] = None


class ExternalService(BaseSchemaModel):
    user: Optional[StrictStr] = None
    password: Optional[StrictStr] = None
    host: Optional[StrictStr] = None
    port: Optional[StrictInt] = None
    database: Optional[StrictStr] = None
    use_password: Optional[bool] = Field(alias="usePassword", default=None)
    conn_max_age: Optional[StrictInt] = Field(alias="connMaxAge", default=None)
    pgbouncer: Optional[Dict] = None
    options: Optional[Dict] = None
    use_resolver: Optional[bool] = Field(alias="useResolver", default=None)
    corporate_proxy: Optional[StrictStr] = Field(alias="corporateProxy", default=None)


class ExternalBackend(BaseSchemaModel):
    enabled: Optional[bool] = None
    backend: Optional[StrictStr] = None
    url: Optional[StrictStr] = None
    options: Optional[Dict] = None


class AuthServicesConfig(BaseSchemaModel):
    github: Optional[ExternalBackend] = None
    gitlab: Optional[ExternalBackend] = None
    bitbucket: Optional[ExternalBackend] = None
    google: Optional[ExternalBackend] = None
    okta: Optional[ExternalBackend] = None
    onelogin: Optional[ExternalBackend] = None
    azuread: Optional[ExternalBackend] = None


class ExternalServicesConfig(BaseSchemaModel):
    redis: Optional[ExternalService] = None
    rabbitmq: Optional[ExternalService] = None
    postgresql: Optional[ExternalService] = None
    gateway: Optional[ExternalService] = None
    api: Optional[ExternalService] = None
    transactions: Optional[ExternalBackend] = None
    analytics: Optional[ExternalBackend] = None
    metrics: Optional[ExternalBackend] = None
    errors: Optional[ExternalBackend] = None
    auth: Optional[AuthServicesConfig] = None
    allowed_versions: Optional[List[StrictStr]] = Field(
        alias="allowedVersions", default=None
    )
