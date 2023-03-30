#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

from typing import Dict, List, Optional

from pydantic import Extra, Field, PrivateAttr, StrictStr, validator

from polyaxon.auxiliaries import (
    V1DefaultScheduling,
    V1PolyaxonCleaner,
    V1PolyaxonInitContainer,
    V1PolyaxonNotifier,
    V1PolyaxonSidecarContainer,
)
from polyaxon.contexts import paths as ctx_paths
from polyaxon.env_vars.keys import (
    EV_KEYS_AGENT_ARTIFACTS_STORE,
    EV_KEYS_AGENT_CLEANER,
    EV_KEYS_AGENT_COMPRESSED_LOGS,
    EV_KEYS_AGENT_CONNECTIONS,
    EV_KEYS_AGENT_DEFAULT_IMAGE_PULL_SECRETS,
    EV_KEYS_AGENT_DEFAULT_SCHEDULING,
    EV_KEYS_AGENT_INIT,
    EV_KEYS_AGENT_IS_REPLICA,
    EV_KEYS_AGENT_NOTIFIER,
    EV_KEYS_AGENT_RUNS_SA,
    EV_KEYS_AGENT_SECRET_NAME,
    EV_KEYS_AGENT_SIDECAR,
    EV_KEYS_AGENT_SPAWNER_REFRESH_INTERVAL,
    EV_KEYS_AGENT_USE_PROXY_ENV_VARS_IN_OPS,
    EV_KEYS_K8S_APP_SECRET_NAME,
    EV_KEYS_K8S_NAMESPACE,
)
from polyaxon.exceptions import PolyaxonSchemaError
from polyaxon.lifecycle import V1ProjectFeature
from polyaxon.parser import parser
from polyaxon.schemas.base import BaseSchemaModel, skip_partial, to_partial
from polyaxon.schemas.types import V1ConnectionType, V1K8sResourceType


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


class BaseAgentConfig(BaseSchemaModel):
    _REQUIRED_ARTIFACTS_STORE = True

    artifacts_store: Optional[V1ConnectionType] = Field(
        alias=EV_KEYS_AGENT_ARTIFACTS_STORE
    )
    connections: Optional[List[V1ConnectionType]] = Field(
        alias=EV_KEYS_AGENT_CONNECTIONS
    )
    namespace: Optional[StrictStr] = Field(alias=EV_KEYS_K8S_NAMESPACE)
    _all_connections: List[V1ConnectionType] = PrivateAttr()
    _secrets: Optional[V1K8sResourceType] = PrivateAttr()
    _config_maps: Optional[V1K8sResourceType] = PrivateAttr()
    _connections_by_names: Dict[str, V1ConnectionType] = PrivateAttr()

    class Config:
        extra = Extra.ignore

    def __init__(
        self,
        **data,
    ):
        super().__init__(**data)
        # Post init
        self._all_connections = []
        self.set_all_connections()
        self._secrets = None
        self._config_maps = None
        self._connections_by_names = {}

    @validator("connections", pre=True)
    def validate_json_list(cls, v):
        if not isinstance(v, str):
            return v
        try:
            return parser.get_dict(
                key=EV_KEYS_AGENT_CONNECTIONS,
                value=v,
                is_list=True,
                is_optional=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError("Received an invalid connections") from e

    @validator("artifacts_store", pre=True)
    def validate_json(cls, v):
        if not isinstance(v, str):
            return v
        try:
            return parser.get_dict(
                key=EV_KEYS_AGENT_ARTIFACTS_STORE,
                value=v,
                is_optional=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(
                "Received an invalid artifacts store `{}`".format(v)
            ) from e

    @validator("connections")
    @skip_partial
    def validate_connections(cls, connections, values):
        try:
            validate_agent_config(
                values.get("artifacts_store"),
                connections,
                cls._REQUIRED_ARTIFACTS_STORE,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(e)
        return connections

    def set_all_connections(self) -> None:
        self._all_connections = self.connections[:] if self.connections else []
        if self.artifacts_store:
            self._all_connections.append(self.artifacts_store)
            validate_agent_config(self.artifacts_store, self.connections)

    @property
    def all_connections(self) -> List[V1ConnectionType]:
        return self._all_connections

    @property
    def secrets(self) -> List[V1K8sResourceType]:
        if self._secrets or not self._all_connections:
            return self._secrets
        secret_names = set()
        secrets = []
        for c in self._all_connections:
            if c.secret and c.secret.name not in secret_names:
                secret_names.add(c.secret.name)
                secrets.append(c.get_secret())
        self._secrets = secrets
        return self._secrets

    @property
    def config_maps(self) -> List[V1K8sResourceType]:
        if self._config_maps or not self._all_connections:
            return self._config_maps
        config_map_names = set()
        config_maps = []
        for c in self._all_connections:
            if c.config_map and c.config_map.name not in config_map_names:
                config_map_names.add(c.config_map.name)
                config_maps.append(c.get_config_map())
        self._config_maps = config_maps
        return self._config_maps

    @property
    def connections_by_names(self) -> Dict[str, V1ConnectionType]:
        if self._connections_by_names or not self._all_connections:
            return self._connections_by_names

        self._connections_by_names = {c.name: c for c in self._all_connections}
        return self._connections_by_names

    @property
    def local_root(self) -> str:
        artifacts_root = ctx_paths.CONTEXT_ARTIFACTS_ROOT
        if not self.artifacts_store:
            return artifacts_root

        if self.artifacts_store.is_mount:
            return self.artifacts_store.store_path

        return artifacts_root

    def get_local_path(self, subpath: str, entity: str = None) -> str:
        full_path = self.local_root
        if entity == V1ProjectFeature.RUNTIME:
            from polyaxon.services.values import PolyaxonServices

            if PolyaxonServices.is_sandbox():
                full_path = os.path.join(full_path, "runs")
        else:
            full_path = os.path.join(full_path, f"{entity}s")

        return f"{full_path}/{subpath}"

    @property
    def store_root(self) -> str:
        artifacts_root = ctx_paths.CONTEXT_ARTIFACTS_ROOT
        if not self.artifacts_store:
            return artifacts_root

        return self.artifacts_store.store_path

    def get_store_path(self, subpath: str, entity: str = None) -> str:
        full_path = self.store_root
        if entity == V1ProjectFeature.RUNTIME:
            from polyaxon.services.values import PolyaxonServices

            if PolyaxonServices.is_sandbox():
                full_path = os.path.join(full_path, "runs")
        else:
            full_path = os.path.join(full_path, f"{entity}s")

        if subpath:
            full_path = os.path.join(full_path, subpath)
        return full_path


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
    spawner_refresh_interval: Optional[int] = Field(
        alias=EV_KEYS_AGENT_SPAWNER_REFRESH_INTERVAL
    )

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
            return parser.get_dict(
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
            return parser.get_string(
                key=field.alias,
                value=v,
                is_optional=True,
                is_list=True,
            )
        except PolyaxonSchemaError as e:
            raise ValueError(
                "Received an invalid {} `{}`".format(field.alias, v)
            ) from e

    def get_spawner_refresh_interval(self) -> int:
        return self.spawner_refresh_interval or 60 * 5


PartialAgentConfig = to_partial(AgentConfig)
