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

from typing import Any, Iterable, List, Optional

from clipped.utils.enums import get_enum_value
from clipped.utils.json import orjson_dumps, orjson_loads
from clipped.utils.lists import to_list

from polyaxon.connections import CONNECTION_CONFIG, V1Connection, V1ConnectionResource
from polyaxon.docker import docker_types
from polyaxon.env_vars.keys import (
    EV_KEYS_API_VERSION,
    EV_KEYS_AUTH_TOKEN,
    EV_KEYS_AUTHENTICATION_TYPE,
    EV_KEYS_HEADER,
    EV_KEYS_HEADER_SERVICE,
    EV_KEYS_HOST,
    EV_KEYS_IS_MANAGED,
    EV_KEYS_K8S_NAMESPACE,
    EV_KEYS_K8S_NODE_NAME,
    EV_KEYS_K8S_POD_ID,
    EV_KEYS_LOG_LEVEL,
    EV_KEYS_RUN_INSTANCE,
    EV_KEYS_SECRET_INTERNAL_TOKEN,
    EV_KEYS_SECRET_KEY,
)
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.services.headers import PolyaxonServiceHeaders


def get_env_var(name: str, value: Any) -> docker_types.V1EnvVar:
    if not isinstance(value, str):
        try:
            value = orjson_dumps(value)
        except (ValueError, TypeError) as e:
            raise PolyaxonConverterError(e)

    return name, value


def get_kv_env_vars(kv_env_vars: List[List]) -> List[docker_types.V1EnvVar]:
    env_vars = []
    if not kv_env_vars:
        return env_vars

    for kv_env_var in kv_env_vars:
        if not kv_env_var or not len(kv_env_var) == 2:
            raise PolyaxonConverterError(
                "Received a wrong a key value env var `{}`".format(kv_env_var)
            )
        env_vars.append(get_env_var(name=kv_env_var[0], value=kv_env_var[1]))

    return env_vars


def get_from_json_resource(
    resource: V1ConnectionResource,
) -> List[docker_types.V1EnvVar]:
    if not resource or resource.items or resource.mount_path:
        return []

    secret = os.environ.get(resource.name)
    if not secret:
        return []
    try:
        secret_value = orjson_loads(secret)
    except Exception as e:
        raise PolyaxonConverterError from e

    return list(secret_value.items())


def get_item_from_json_env_var(
    key: str, resource_ref_name: str
) -> Optional[docker_types.V1EnvVar]:
    secret = os.environ.get(resource_ref_name)
    if not secret:
        return None
    try:
        secret_value = orjson_loads(secret)
    except Exception as e:
        raise PolyaxonConverterError from e

    value = secret_value.get(key)
    return key, value


def get_items_from_json_env_var(
    resource: V1ConnectionResource,
) -> List[docker_types.V1EnvVar]:
    items_from = []
    if not resource or not resource.items:
        return items_from

    for item in resource.items:
        value = get_item_from_json_env_var(
            key=item,
            resource_ref_name=resource.name,
        )
        if value:
            items_from.append(value)
    return items_from


def get_env_vars_from_resources(
    resources: Iterable[V1ConnectionResource],
) -> List[docker_types.V1EnvVar]:
    resources = resources or []
    env_vars = []
    for secret in resources:
        env_vars += get_items_from_json_env_var(resource=secret)
    return env_vars


def get_env_from_json_resources(
    resources: Iterable[V1ConnectionResource],
) -> List[docker_types.V1EnvVar]:
    resources = resources or []
    results = []
    for resource in resources:
        results += get_from_json_resource(resource=resource)
    return [r for r in results if r]


def get_base_env_vars(
    namespace: str,
    resource_name: str,
    use_proxy_env_vars_use_in_ops: bool,
    log_level: Optional[str] = None,
):
    env = [
        get_env_var(name=EV_KEYS_K8S_NODE_NAME, value="docker-agent"),
        get_env_var(name=EV_KEYS_K8S_NAMESPACE, value=namespace),
        get_env_var(name=EV_KEYS_K8S_POD_ID, value=resource_name),
    ]
    if log_level:
        env.append(get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level))
    env += get_proxy_env_vars(use_proxy_env_vars_use_in_ops)
    return env


def get_service_env_vars(
    header: str,
    service_header: str,
    include_secret_key: bool,
    include_internal_token: bool,
    include_agent_token: bool,
    authentication_type: str,
    polyaxon_default_secret_ref: str,
    polyaxon_agent_secret_ref: str,
    api_host: str,
    api_version: str,
    run_instance: str,
    namespace: str,
    resource_name: str,
    use_proxy_env_vars_use_in_ops: bool,
    log_level: str,
) -> List[docker_types.V1EnvVar]:
    env_vars = get_base_env_vars(
        namespace=namespace,
        resource_name=resource_name,
        use_proxy_env_vars_use_in_ops=use_proxy_env_vars_use_in_ops,
    ) + [
        get_env_var(name=EV_KEYS_HOST, value=api_host),
        get_env_var(name=EV_KEYS_IS_MANAGED, value=True),
        get_env_var(name=EV_KEYS_API_VERSION, value=api_version),
        get_run_instance_env_var(run_instance),
    ]
    if log_level:
        env_vars.append(get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level))
    if header:
        env_vars.append(
            get_env_var(
                name=EV_KEYS_HEADER,
                value=PolyaxonServiceHeaders.get_header(header),
            )
        )
    if service_header:
        env_vars.append(
            get_env_var(
                name=EV_KEYS_HEADER_SERVICE, value=get_enum_value(service_header)
            )
        )
    if include_secret_key:
        env_vars.append(
            get_item_from_json_env_var(
                key=EV_KEYS_SECRET_KEY,
                resource_ref_name=polyaxon_default_secret_ref,
            )
        )
    internal = False
    if include_internal_token and polyaxon_default_secret_ref:
        internal = True
        env_vars.append(
            get_item_from_json_env_var(
                key=EV_KEYS_SECRET_INTERNAL_TOKEN,
                resource_ref_name=polyaxon_default_secret_ref,
            )
        )
    if include_agent_token and polyaxon_agent_secret_ref:
        if internal:
            raise PolyaxonConverterError(
                "A service cannot have internal token and agent token."
            )
        env_vars.append(
            get_item_from_json_env_var(
                key=EV_KEYS_AUTH_TOKEN,
                resource_ref_name=polyaxon_agent_secret_ref,
            )
        )
    if authentication_type:
        env_vars.append(
            get_env_var(name=EV_KEYS_AUTHENTICATION_TYPE, value=authentication_type)
        )
    return env_vars


def get_run_instance_env_var(run_instance: str) -> docker_types.V1EnvVar:
    return get_env_var(name=EV_KEYS_RUN_INSTANCE, value=run_instance)


def get_connection_env_var(connection: V1Connection) -> List[docker_types.V1EnvVar]:
    env_vars = []
    if not connection:
        return env_vars

    if connection.env:
        env_vars += to_list(connection.env, check_none=True)

    return env_vars


def get_connections_catalog_env_var(
    connections: List[V1Connection],
) -> Optional[docker_types.V1EnvVar]:
    catalog = CONNECTION_CONFIG.get_connections_catalog(connections)
    if not catalog:
        return None
    return get_env_var(
        name=CONNECTION_CONFIG.get_connections_catalog_env_name(),
        value=catalog.to_json(),
    )


def get_proxy_env_var(key: str) -> Optional[str]:
    value = os.environ.get(key)
    if not value:
        value = os.environ.get(key.lower())
    if not value:
        value = os.environ.get(key.upper())

    return value


def add_proxy_env_var(name: str, value: str) -> List[docker_types.V1EnvVar]:
    return [
        get_env_var(name.upper(), value),
        get_env_var(name, value),
    ]


def get_proxy_env_vars(
    use_proxy_env_vars_use_in_ops: bool,
) -> List[docker_types.V1EnvVar]:
    if use_proxy_env_vars_use_in_ops:
        env_vars = []
        https_proxy = get_proxy_env_var("HTTPS_PROXY")
        if not https_proxy:
            https_proxy = get_proxy_env_var("https_proxy")
        if https_proxy:
            env_vars += add_proxy_env_var(name="HTTPS_PROXY", value=https_proxy)
            env_vars += add_proxy_env_var(name="https_proxy", value=https_proxy)
        http_proxy = get_proxy_env_var("HTTP_PROXY")
        if not http_proxy:
            http_proxy = get_proxy_env_var("http_proxy")
        if http_proxy:
            env_vars += add_proxy_env_var(name="HTTP_PROXY", value=http_proxy)
            env_vars += add_proxy_env_var(name="http_proxy", value=http_proxy)
        no_proxy = get_proxy_env_var("NO_PROXY")
        if not no_proxy:
            no_proxy = get_proxy_env_var("no_proxy")
        if no_proxy:
            env_vars += add_proxy_env_var(name="NO_PROXY", value=no_proxy)
            env_vars += add_proxy_env_var(name="no_proxy", value=no_proxy)
        return env_vars
    return []
