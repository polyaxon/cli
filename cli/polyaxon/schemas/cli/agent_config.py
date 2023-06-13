import os

from typing import Dict, List, Optional

from clipped.config.schema import skip_partial, to_partial
from pydantic import Extra, Field, StrictStr, root_validator, validator
from vents.connections import ConnectionCatalog

from polyaxon.auxiliaries import (
    V1DefaultScheduling,
    V1PolyaxonCleaner,
    V1PolyaxonInitContainer,
    V1PolyaxonNotifier,
    V1PolyaxonSidecarContainer,
)
from polyaxon.config.parser import ConfigParser
from polyaxon.connections import V1Connection, V1ConnectionKind, V1HostPathConnection
from polyaxon.contexts import paths as ctx_paths
from polyaxon.env_vars.getters import get_artifacts_store_name
from polyaxon.env_vars.keys import (
    EV_KEYS_AGENT_ARTIFACTS_STORE,
    EV_KEYS_AGENT_CLEANER,
    EV_KEYS_AGENT_COMPRESSED_LOGS,
    EV_KEYS_AGENT_CONNECTIONS,
    EV_KEYS_AGENT_DEFAULT_IMAGE_PULL_SECRETS,
    EV_KEYS_AGENT_DEFAULT_SCHEDULING,
    EV_KEYS_AGENT_EXECUTOR_REFRESH_INTERVAL,
    EV_KEYS_AGENT_INIT,
    EV_KEYS_AGENT_IS_REPLICA,
    EV_KEYS_AGENT_NOTIFIER,
    EV_KEYS_AGENT_RUNS_SA,
    EV_KEYS_AGENT_SECRET_NAME,
    EV_KEYS_AGENT_SIDECAR,
    EV_KEYS_AGENT_USE_PROXY_ENV_VARS_IN_OPS,
    EV_KEYS_ARTIFACTS_STORE_NAME,
    EV_KEYS_K8S_APP_SECRET_NAME,
    EV_KEYS_K8S_NAMESPACE,
)
from polyaxon.exceptions import PolyaxonSchemaError
from polyaxon.fs.utils import get_store_path
from polyaxon.schemas.base import BaseSchemaModel


def validate_agent_config(
    artifacts_store, connections, required_artifacts_store: bool = True
) -> None:
    if required_artifacts_store and not artifacts_store:
        raise PolyaxonSchemaError(
            "A connection definition is required to set a default artifacts store."
        )

    connections = connections or []

    connection_names = set()

    if artifacts_store:
        connection_names.add(artifacts_store.name)

    for c in connections:
        if c.name in connection_names:
            raise PolyaxonSchemaError(
                "A connection with name `{}` must be unique.".format(c.name)
            )
        connection_names.add(c.name)


class BaseAgentConfig(ConnectionCatalog, BaseSchemaModel):
    _REQUIRED_ARTIFACTS_STORE = True

    connections: Optional[List[V1Connection]] = Field(alias=EV_KEYS_AGENT_CONNECTIONS)
    artifacts_store: Optional[V1Connection] = Field(alias=EV_KEYS_AGENT_ARTIFACTS_STORE)
    namespace: Optional[StrictStr] = Field(alias=EV_KEYS_K8S_NAMESPACE)

    class Config:
        extra = Extra.ignore

    @root_validator(pre=True)
    def handle_camel_case_artifacts_store(cls, values):
        if (
            not values.get("artifacts_store")
            and not values.get(EV_KEYS_AGENT_ARTIFACTS_STORE)
            and "artifactsStore" in values
        ):
            values[EV_KEYS_AGENT_ARTIFACTS_STORE] = values["artifactsStore"]
        return values

    @validator("connections", pre=True)
    def validate_json_list(cls, v):
        if not isinstance(v, str):
            return v
        try:
            return ConfigParser.parse(Dict)(
                key=EV_KEYS_AGENT_CONNECTIONS,
                value=v,
                is_list=True,
                is_optional=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError("Received an invalid connections") from e

    @validator("artifacts_store", pre=True)
    def validate_store_json(cls, v):
        if not isinstance(v, str):
            return v
        try:
            return ConfigParser.parse(Dict)(
                key=EV_KEYS_AGENT_ARTIFACTS_STORE,
                value=v,
                is_optional=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(
                "Received an invalid artifacts store `{}`".format(v)
            ) from e

    @validator("artifacts_store")
    @skip_partial
    def validate_agent_config(cls, artifacts_store, values):
        try:
            validate_agent_config(
                artifacts_store,
                values.get("connections"),
                cls._REQUIRED_ARTIFACTS_STORE,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(e)
        return artifacts_store

    def set_all_connections(self) -> None:
        self._all_connections = self.connections[:] if self.connections else []
        self._connections_by_names = {}
        if self.artifacts_store:
            self._all_connections.append(self.artifacts_store)
            validate_agent_config(
                self.artifacts_store, self.connections, self._REQUIRED_ARTIFACTS_STORE
            )

    @property
    def local_root(self) -> str:
        artifacts_root = ctx_paths.CONTEXT_ARTIFACTS_ROOT
        if not self.artifacts_store:
            return artifacts_root

        if self.artifacts_store.is_mount:
            return self.artifacts_store.store_path

        return artifacts_root

    def get_local_path(self, subpath: str, entity: Optional[str] = None) -> str:
        return get_store_path(
            store_path=self.local_root, subpath=subpath, entity=entity
        )

    @property
    def store_root(self) -> str:
        if not self.artifacts_store:
            return ctx_paths.CONTEXT_ARTIFACTS_ROOT

        return self.artifacts_store.store_path

    def get_store_path(self, subpath: str, entity: Optional[str] = None) -> str:
        return get_store_path(
            store_path=self.store_root, subpath=subpath, entity=entity
        )

    def set_default_artifacts_store(self):
        if not self.artifacts_store:
            self.artifacts_store = V1Connection(
                name=get_artifacts_store_name(),
                kind=V1ConnectionKind.HOST_PATH,
                schema_=V1HostPathConnection(
                    host_path=self.store_root, mount_path=self.store_root
                ),
            )
            self.set_all_connections()

    def set_artifacts_store_name(self):
        if self.artifacts_store:
            os.environ[EV_KEYS_ARTIFACTS_STORE_NAME] = self.artifacts_store.name


class AgentConfig(BaseAgentConfig):
    _IDENTIFIER = "agent"

    is_replica: Optional[bool] = Field(alias=EV_KEYS_AGENT_IS_REPLICA)
    compressed_logs: Optional[bool] = Field(alias=EV_KEYS_AGENT_COMPRESSED_LOGS)
    sidecar: Optional[V1PolyaxonSidecarContainer] = Field(alias=EV_KEYS_AGENT_SIDECAR)
    init: Optional[V1PolyaxonInitContainer] = Field(alias=EV_KEYS_AGENT_INIT)
    notifier: Optional[V1PolyaxonNotifier] = Field(alias=EV_KEYS_AGENT_NOTIFIER)
    cleaner: Optional[V1PolyaxonCleaner] = Field(alias=EV_KEYS_AGENT_CLEANER)
    use_proxy_env_vars_use_in_ops: Optional[bool] = Field(
        alias=EV_KEYS_AGENT_USE_PROXY_ENV_VARS_IN_OPS
    )
    default_scheduling: Optional[V1DefaultScheduling] = Field(
        alias=EV_KEYS_AGENT_DEFAULT_SCHEDULING
    )
    default_image_pull_secrets: Optional[List[StrictStr]] = Field(
        alias=EV_KEYS_AGENT_DEFAULT_IMAGE_PULL_SECRETS
    )
    app_secret_name: Optional[StrictStr] = Field(alias=EV_KEYS_K8S_APP_SECRET_NAME)
    agent_secret_name: Optional[StrictStr] = Field(alias=EV_KEYS_AGENT_SECRET_NAME)
    runs_sa: Optional[StrictStr] = Field(alias=EV_KEYS_AGENT_RUNS_SA)
    # This refresh logic will mitigate several issues with AKS's numerous networking problems
    executor_refresh_interval: Optional[int] = Field(
        alias=EV_KEYS_AGENT_EXECUTOR_REFRESH_INTERVAL
    )

    @root_validator(pre=True)
    def handle_camel_case_agent(cls, values):
        if (
            not values.get("is_replica")
            and not values.get(EV_KEYS_AGENT_IS_REPLICA)
            and "isReplica" in values
        ):
            values[EV_KEYS_AGENT_IS_REPLICA] = values["artifactsStore"]
        if (
            not values.get("use_proxy_env_vars_use_in_ops")
            and not values.get(EV_KEYS_AGENT_USE_PROXY_ENV_VARS_IN_OPS)
            and "useProxyEnvVarsUseInOps" in values
        ):
            values[EV_KEYS_AGENT_USE_PROXY_ENV_VARS_IN_OPS] = values[
                "useProxyEnvVarsUseInOps"
            ]
        if (
            not values.get("default_scheduling")
            and not values.get(EV_KEYS_AGENT_DEFAULT_SCHEDULING)
            and "defaultScheduling" in values
        ):
            values[EV_KEYS_AGENT_DEFAULT_SCHEDULING] = values["defaultScheduling"]
        if (
            not values.get("default_image_pull_secrets")
            and not values.get(EV_KEYS_AGENT_DEFAULT_IMAGE_PULL_SECRETS)
            and "defaultImagePullSecrets" in values
        ):
            values[EV_KEYS_AGENT_DEFAULT_IMAGE_PULL_SECRETS] = values[
                "defaultImagePullSecrets"
            ]
        if (
            not values.get("app_secret_name")
            and not values.get(EV_KEYS_K8S_APP_SECRET_NAME)
            and "appSecretName" in values
        ):
            values[EV_KEYS_K8S_APP_SECRET_NAME] = values["appSecretName"]
        if (
            not values.get("agent_secret_name")
            and not values.get(EV_KEYS_AGENT_SECRET_NAME)
            and "agentSecretName" in values
        ):
            values[EV_KEYS_AGENT_SECRET_NAME] = values["agentSecretName"]
        if (
            not values.get("runs_sa")
            and not values.get(EV_KEYS_AGENT_RUNS_SA)
            and "runsSa" in values
        ):
            values[EV_KEYS_AGENT_RUNS_SA] = values["runsSa"]
        if (
            not values.get("executor_refresh_interval")
            and not values.get(EV_KEYS_AGENT_EXECUTOR_REFRESH_INTERVAL)
            and "executorRefreshInterval" in values
        ):
            values[EV_KEYS_AGENT_EXECUTOR_REFRESH_INTERVAL] = values[
                "executorRefreshInterval"
            ]
        return values

    def __init__(
        self,
        default_scheduling=None,
        default_image_pull_secrets=None,
        **data,
    ):
        if not default_scheduling and default_image_pull_secrets:
            default_scheduling = V1DefaultScheduling()
        if default_scheduling and not default_scheduling.image_pull_secrets:
            default_scheduling.image_pull_secrets = default_image_pull_secrets
        super().__init__(
            default_scheduling=default_scheduling,
            default_image_pull_secrets=default_image_pull_secrets,
            **data,
        )

    @validator(
        "artifacts_store",
        "sidecar",
        "init",
        "cleaner",
        "notifier",
        "default_scheduling",
        pre=True,
    )
    def validate_json(cls, v, field):
        if not isinstance(v, str):
            return v
        try:
            return ConfigParser.parse(Dict)(
                key=field.name,
                value=v,
                is_optional=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(
                "Received an invalid {} `{}`".format(field.alias, v)
            ) from e

    @validator("default_image_pull_secrets", pre=True)
    def validate_str_list(cls, v, field):
        try:
            return ConfigParser.parse(str)(
                key=field.alias,
                value=v,
                is_optional=True,
                is_list=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(
                "Received an invalid {} `{}`".format(field.alias, v)
            ) from e

    def get_executor_refresh_interval(self) -> int:
        return self.executor_refresh_interval or 60 * 5


PartialAgentConfig = to_partial(AgentConfig)
