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

# Platform
EV_KEYS_PLATFORM_CONFIG = "POLYAXON_PLATFORM_CONFIG"

# General
EV_KEYS_NO_CONFIG = "POLYAXON_NO_CONFIG"
EV_KEYS_SERVICE = "POLYAXON_SERVICE"
EV_KEYS_ENVIRONMENT = "POLYAXON_ENVIRONMENT"
EV_KEYS_HEADER = "POLYAXON_HEADER"
EV_KEYS_HEADER_SERVICE = "POLYAXON_HEADER_SERVICE"
EV_KEYS_AUTHENTICATION_TYPE = "POLYAXON_AUTHENTICATION_TYPE"
EV_KEYS_DEBUG = "POLYAXON_DEBUG"
EV_KEYS_TIMEOUT = "POLYAXON_TIMEOUT"
EV_KEYS_TRACKING_TIMEOUT = "POLYAXON_TRACKING_TIMEOUT"
EV_KEYS_TIME_ZONE = "POLYAXON_TIME_ZONE"
EV_KEYS_WATCH_INTERVAL = "POLYAXON_WATCH_INTERVAL"
EV_KEYS_INTERVAL = "POLYAXON_INTERVAL"
EV_KEYS_LOG_LEVEL = "POLYAXON_LOG_LEVEL"
EV_KEYS_K8S_NAMESPACE = "POLYAXON_K8S_NAMESPACE"
EV_KEYS_K8S_NODE_NAME = "POLYAXON_K8S_NODE_NAME"
EV_KEYS_K8S_POD_ID = "POLYAXON_K8S_POD_ID"
EV_KEYS_PLATFORM_HOST = "POLYAXON_PLATFORM_HOST"
EV_KEYS_HOST = "POLYAXON_HOST"
EV_KEYS_API_VERSION = "POLYAXON_API_VERSION"
EV_KEYS_VERIFY_SSL = "POLYAXON_VERIFY_SSL"
EV_KEYS_SSL_CA_CERT = "POLYAXON_SSL_CA_CERT"
EV_KEYS_CERT_FILE = "POLYAXON_CERT_FILE"
EV_KEYS_KEY_FILE = "POLYAXON_KEY_FILE"
EV_KEYS_ASSERT_HOSTNAME = "POLYAXON_ASSERT_HOSTNAME"
EV_KEYS_CONNECTION_POOL_MAXSIZE = "POLYAXON_CONNECTION_POOL_MAXSIZE"
EV_KEYS_LOGS_ROOT = "POLYAXON_LOG_ROOT"
EV_KEYS_ARCHIVES_ROOT = "POLYAXON_ARCHIVES_ROOT"
EV_KEYS_ARTIFACTS_ROOT = "POLYAXON_ARTIFACTS_ROOT"
EV_KEYS_STATIC_ROOT = "POLYAXON_STATIC_ROOT"
EV_KEYS_CONTEXT_ROOT = "POLYAXON_CONTEXT_ROOT"
EV_KEYS_OFFLINE_ROOT = "POLYAXON_OFFLINE_ROOT"
EV_KEYS_DISABLE_ERRORS_REPORTING = "POLYAXON_DISABLE_ERRORS_REPORTING"
EV_KEYS_INTERVALS_COMPATIBILITY_CHECK = "POLYAXON_INTERVALS_COMPATIBILITY_CHECK"
EV_KEYS_UPLOAD_SIZE = "POLYAXON_UPLOAD_SIZE"

# Secrets
EV_KEYS_SECRET_KEY = "POLYAXON_SECRET_KEY"  # noqa
EV_KEYS_SECRET_INTERNAL_TOKEN = "POLYAXON_SECRET_INTERNAL_TOKEN"  # noqa
EV_KEYS_AUTH_TOKEN = "POLYAXON_AUTH_TOKEN"
EV_KEYS_AUTH_USERNAME = "POLYAXON_AUTH_USERNAME"
EV_KEYS_CUSTOM_ERRORS_OPTIONS = "POLYAXON_CUSTOM_ERRORS_OPTIONS"

# Containers
EV_KEYS_AGENT_INSTANCE = "POLYAXON_AGENT_INSTANCE"
EV_KEYS_RUN_INSTANCE = "POLYAXON_RUN_INSTANCE"
EV_KEYS_CONTAINER_ID = "POLYAXON_CONTAINER_ID"
EV_KEYS_HASH_LENGTH = "POLYAXON_HASH_LENGTH"

# Flags
EV_KEYS_K8S_IN_CLUSTER = "POLYAXON_K8S_IN_CLUSTER"
EV_KEYS_IS_MANAGED = "POLYAXON_IS_MANAGED"
EV_KEYS_IS_OFFLINE = "POLYAXON_IS_OFFLINE"
EV_KEYS_NO_OP = "POLYAXON_NO_OP"
EV_KEYS_NO_API = "POLYAXON_NO_API"

# Registry
EV_KEYS_USE_GIT_REGISTRY = "POLYAXON_USE_GIT_REGISTRY"
EV_KEYS_PUBLIC_REGISTRY = "POLYAXON_PUBLIC_REGISTRY"

# Agent
EV_KEYS_AGENT_SIDECAR = "POLYAXON_AGENT_SIDECAR"
EV_KEYS_AGENT_INIT = "POLYAXON_AGENT_INIT"
EV_KEYS_AGENT_CLEANER = "POLYAXON_AGENT_CLEANER"
EV_KEYS_AGENT_NOTIFIER = "POLYAXON_AGENT_NOTIFIER"
EV_KEYS_AGENT_DEFAULT_SCHEDULING = "POLYAXON_AGENT_DEFAULT_SCHEDULING"
EV_KEYS_AGENT_DEFAULT_IMAGE_PULL_SECRETS = "POLYAXON_AGENT_DEFAULT_IMAGE_PULL_SECRETS"
EV_KEYS_AGENT_ARTIFACTS_STORE = "POLYAXON_AGENT_ARTIFACTS_STORE"
EV_KEYS_AGENT_CONNECTIONS = "POLYAXON_AGENT_CONNECTIONS"
EV_KEYS_SET_AGENT = "POLYAXON_SET_AGENT"
EV_KEYS_K8S_APP_SECRET_NAME = "POLYAXON_K8S_APP_SECRET_NAME"  # noqa
EV_KEYS_AGENT_SECRET_NAME = "POLYAXON_AGENT_SECRET_NAME"  # noqa
EV_KEYS_AGENT_RUNS_SA = "POLYAXON_AGENT_RUNS_SA"
EV_KEYS_AGENT_SPAWNER_REFRESH_INTERVAL = "POLYAXON_AGENT_SPAWNER_REFRESH_INTERVAL"
EV_KEYS_AGENT_IS_REPLICA = "POLYAXON_AGENT_IS_REPLICA"
EV_KEYS_AGENT_COMPRESSED_LOGS = "POLYAXON_AGENT_COMPRESSED_LOGS"
EV_KEYS_AGENT_USE_PROXY_ENV_VARS_IN_OPS = "POLYAXON_AGENT_USE_PROXY_ENV_VARS_IN_OPS"

# Connections
EV_KEYS_COLLECT_ARTIFACTS = "POLYAXON_COLLECT_ARTIFACTS"
EV_KEYS_COLLECT_RESOURCES = "POLYAXON_COLLECT_RESOURCES"
EV_KEYS_ARTIFACTS_STORE_NAME = "POLYAXON_ARTIFACTS_STORE_NAME"
EV_KEYS_GIT_CREDENTIALS = "POLYAXON_GIT_CREDENTIALS"
EV_KEYS_GIT_CREDENTIALS_STORE = "POLYAXON_GIT_CREDENTIALS_STORE"
EV_KEYS_SSH_PATH = "POLYAXON_SSH_PATH"
EV_KEYS_SSH_PRIVATE_KEY = "POLYAXON_SSH_PRIVATE_KEY"
EV_KEYS_CONNECTION_CONTEXT_PATH_FORMAT = "POLYAXON_CONNECTION_CONTEXT_PATH_{}"
EV_KEYS_CONNECTION_SCHEMA_FORMAT = "POLYAXON_CONNECTION_SCHEMA_{}"

# Ops
EV_KEYS_ISTIO_ENABLED = "POLYAXON_ISTIO_ENABLED"
EV_KEYS_SPARK_ENABLED = "POLYAXON_SPARK_ENABLED"
EV_KEYS_DASK_ENABLED = "POLYAXON_DASK_ENABLED"
EV_KEYS_FLINK_ENABLED = "POLYAXON_FLINK_ENABLED"
EV_KEYS_TFJOB_ENABLED = "POLYAXON_TFJOB_ENABLED"
EV_KEYS_PYTORCH_JOB_ENABLED = "POLYAXON_PYTORCH_JOB_ENABLED"
EV_KEYS_MXJOB_ENABLED = "POLYAXON_MXJOB_ENABLED"
EV_KEYS_XGBOOST_JOB_ENABLED = "POLYAXON_XGBOOST_JOB_ENABLED"
EV_KEYS_MPIJOB_ENABLED = "POLYAXON_MPIJOB_ENABLED"

# Sandbox
EV_KEYS_SANDBOX_PORT = "POLYAXON_SANDBOX_PORT"
EV_KEYS_SANDBOX_HOST = "POLYAXON_SANDBOX_HOST"
EV_KEYS_SANDBOX_DEBUG = "POLYAXON_SANDBOX_DEBUG"
EV_KEYS_SANDBOX_SSL_ENABLED = "POLYAXON_SANDBOX_SSL_ENABLED"
EV_KEYS_SANDBOX_WORKERS = "POLYAXON_SANDBOX_WORKERS"
EV_KEYS_SANDBOX_PER_CORE = "POLYAXON_SANDBOX_PER_CORE"
EV_KEYS_SANDBOX_IS_LOCAL = "POLYAXON_SANDBOX_IS_LOCAL"
EV_KEYS_SANDBOX_ROOT = "POLYAXON_SANDBOX_ROOT"

# Proxies
EV_KEYS_PROXY_NAMESPACES = "POLYAXON_PROXY_NAMESPACES"
EV_KEYS_PROXY_GATEWAY_PORT = "POLYAXON_PROXY_GATEWAY_PORT"
EV_KEYS_PROXY_GATEWAY_TARGET_PORT = "POLYAXON_PROXY_GATEWAY_TARGET_PORT"
EV_KEYS_PROXY_GATEWAY_HOST = "POLYAXON_PROXY_GATEWAY_HOST"
EV_KEYS_PROXY_STREAMS_PORT = "POLYAXON_PROXY_STREAMS_PORT"
EV_KEYS_PROXY_STREAMS_TARGET_PORT = "POLYAXON_PROXY_STREAMS_TARGET_PORT"
EV_KEYS_PROXY_STREAMS_HOST = "POLYAXON_PROXY_STREAMS_HOST"
EV_KEYS_PROXY_API_PORT = "POLYAXON_PROXY_API_PORT"
EV_KEYS_PROXY_API_TARGET_PORT = "POLYAXON_PROXY_API_TARGET_PORT"
EV_KEYS_PROXY_API_HOST = "POLYAXON_PROXY_API_HOST"
EV_KEYS_PROXY_LOCAL_PORT = "POLYAXON_PROXY_LOCAL_PORT"
EV_KEYS_PROXY_API_USE_RESOLVER = "POLYAXON_PROXY_API_USE_RESOLVER"
EV_KEYS_PROXY_SERVICES_PORT = "POLYAXON_PROXY_SERVICES_PORT"
EV_KEYS_PROXY_SSL_PATH = "POLYAXON_PROXY_SSL_PATH"
EV_KEYS_PROXY_SSL_ENABLED = "POLYAXON_PROXY_SSL_ENABLED"
EV_KEYS_PROXY_AUTH_ENABLED = "POLYAXON_PROXY_AUTH_ENABLED"
EV_KEYS_PROXY_AUTH_EXTERNAL = "POLYAXON_PROXY_AUTH_EXTERNAL"
EV_KEYS_PROXY_AUTH_USE_RESOLVER = "POLYAXON_PROXY_AUTH_USE_RESOLVER"
EV_KEYS_PROXY_HAS_FORWARD_PROXY = "POLYAXON_PROXY_HAS_FORWARD_PROXY"
EV_KEYS_PROXY_FORWARD_PROXY_PORT = "POLYAXON_PROXY_FORWARD_PROXY_PORT"
EV_KEYS_PROXY_FORWARD_PROXY_HOST = "POLYAXON_PROXY_FORWARD_PROXY_HOST"
EV_KEYS_PROXY_FORWARD_PROXY_KIND = "POLYAXON_PROXY_FORWARD_PROXY_KIND"
EV_KEYS_UI_IN_SANDBOX = "POLYAXON_UI_IN_SANDBOX"
EV_KEYS_UI_ADMIN_ENABLED = "POLYAXON_UI_ADMIN_ENABLED"
EV_KEYS_UI_ASSETS_VERSION = "POLYAXON_UI_ASSETS_VERSION"
EV_KEYS_UI_ENABLED = "POLYAXON_UI_ENABLED"
EV_KEYS_UI_OFFLINE = "POLYAXON_UI_OFFLINE"
EV_KEYS_UI_BASE_URL = "POLYAXON_UI_BASE_URL"
EV_KEYS_STATIC_URL = "POLYAXON_STATIC_URL"
EV_KEYS_DNS_USE_RESOLVER = "POLYAXON_DNS_USE_RESOLVER"
EV_KEYS_DNS_CUSTOM_CLUSTER = "POLYAXON_DNS_CUSTOM_CLUSTER"
EV_KEYS_DNS_BACKEND = "POLYAXON_DNS_BACKEND"
EV_KEYS_DNS_PREFIX = "POLYAXON_DNS_PREFIX"
EV_KEYS_NGINX_TIMEOUT = "POLYAXON_NGINX_TIMEOUT"
EV_KEYS_NGINX_INDENT_CHAR = "POLYAXON_NGINX_INDENT_CHAR"
EV_KEYS_NGINX_INDENT_WIDTH = "POLYAXON_NGINX_INDENT_WIDTH"
