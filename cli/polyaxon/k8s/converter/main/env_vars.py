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

from typing import Iterable, List

from clipped.utils.lists import to_list

from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.env_vars.keys import (
    EV_KEYS_ARTIFACTS_STORE_NAME,
    EV_KEYS_COLLECT_ARTIFACTS,
    EV_KEYS_COLLECT_RESOURCES,
)
from polyaxon.exceptions import PolyaxonSchemaError, PolypodException
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.env_vars import (
    get_connection_env_var,
    get_connections_catalog_env_var,
    get_env_var,
    get_env_vars_from_k8s_resources,
    get_kv_env_vars,
)
from polyaxon.polyflow import V1Plugins


def get_env_vars(
    plugins: V1Plugins,
    kv_env_vars: List[List],
    artifacts_store_name: str,
    connections: Iterable[V1Connection],
    secrets: Iterable[V1ConnectionResource],
    config_maps: Iterable[V1ConnectionResource],
) -> List[k8s_schemas.V1EnvVar]:
    env_vars = []
    connections = connections or []

    if plugins and plugins.collect_artifacts:
        env_vars.append(get_env_var(name=EV_KEYS_COLLECT_ARTIFACTS, value=True))

    if plugins and plugins.collect_resources:
        env_vars.append(get_env_var(name=EV_KEYS_COLLECT_RESOURCES, value=True))

    if artifacts_store_name:
        env_vars.append(
            get_env_var(name=EV_KEYS_ARTIFACTS_STORE_NAME, value=artifacts_store_name)
        )

    # Add connections catalog env vars information
    env_vars += to_list(
        get_connections_catalog_env_var(connections=connections),
        check_none=True,
    )
    # Add connection env vars information
    for connection in connections:
        try:
            secret = connection.secret
            env_vars += to_list(
                get_connection_env_var(connection=connection),
                check_none=True,
            )
        except PolyaxonSchemaError as e:
            raise PolypodException("Error resolving secrets: %s" % e) from e

    env_vars += get_kv_env_vars(kv_env_vars)
    env_vars += get_env_vars_from_k8s_resources(
        secrets=secrets, config_maps=config_maps
    )
    return env_vars
