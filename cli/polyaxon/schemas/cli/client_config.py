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
from typing import Dict, Optional, Union

import urllib3

from pydantic import Extra, Field, StrictStr

from polyaxon.api import LOCALHOST, POLYAXON_CLOUD_HOST
from polyaxon.contexts import paths as ctx_paths
from polyaxon.env_vars.keys import (
    EV_KEYS_API_VERSION,
    EV_KEYS_ARCHIVES_ROOT,
    EV_KEYS_ASSERT_HOSTNAME,
    EV_KEYS_AUTHENTICATION_TYPE,
    EV_KEYS_CERT_FILE,
    EV_KEYS_CONNECTION_POOL_MAXSIZE,
    EV_KEYS_DEBUG,
    EV_KEYS_DISABLE_ERRORS_REPORTING,
    EV_KEYS_HEADER,
    EV_KEYS_HEADER_SERVICE,
    EV_KEYS_HOST,
    EV_KEYS_INTERVAL,
    EV_KEYS_INTERVALS_COMPATIBILITY_CHECK,
    EV_KEYS_IS_MANAGED,
    EV_KEYS_IS_OFFLINE,
    EV_KEYS_K8S_IN_CLUSTER,
    EV_KEYS_K8S_NAMESPACE,
    EV_KEYS_KEY_FILE,
    EV_KEYS_LOG_LEVEL,
    EV_KEYS_NO_API,
    EV_KEYS_NO_OP,
    EV_KEYS_RETRIES,
    EV_KEYS_SSL_CA_CERT,
    EV_KEYS_TIME_ZONE,
    EV_KEYS_TIMEOUT,
    EV_KEYS_TRACKING_TIMEOUT,
    EV_KEYS_VERIFY_SSL,
    EV_KEYS_WATCH_INTERVAL,
)
from polyaxon.exceptions import PolyaxonClientException
from polyaxon.pkg import VERSION
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.sdk.configuration import Configuration
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.services.headers import PolyaxonServiceHeaders
from polyaxon.services.values import PolyaxonServices
from polyaxon.utils.http_utils import clean_host


class ClientConfig(BaseSchemaModel):
    _IDENTIFIER = "global"

    _PAGE_SIZE = 20
    _BASE_URL = "{}/api/{}"

    host: Optional[StrictStr] = Field(alias=EV_KEYS_HOST)
    version: Optional[StrictStr] = Field(default="v1", alias=EV_KEYS_API_VERSION)
    debug: Optional[bool] = Field(default=False, alias=EV_KEYS_DEBUG)
    log_level: Optional[StrictStr] = Field(alias=EV_KEYS_LOG_LEVEL)
    authentication_type: Optional[StrictStr] = Field(
        default=AuthenticationTypes.TOKEN, alias=EV_KEYS_AUTHENTICATION_TYPE
    )
    is_managed: Optional[bool] = Field(default=False, alias=EV_KEYS_IS_MANAGED)
    is_offline: Optional[bool] = Field(default=False, alias=EV_KEYS_IS_OFFLINE)
    in_cluster: Optional[bool] = Field(default=False, alias=EV_KEYS_K8S_IN_CLUSTER)
    no_op: Optional[bool] = Field(default=False, alias=EV_KEYS_NO_OP)
    timeout: Optional[float] = Field(default=20, alias=EV_KEYS_TIMEOUT)
    tracking_timeout: Optional[float] = Field(default=1, alias=EV_KEYS_TRACKING_TIMEOUT)
    timezone: Optional[StrictStr] = Field(alias=EV_KEYS_TIME_ZONE)
    watch_interval: Optional[int] = Field(default=5, alias=EV_KEYS_WATCH_INTERVAL)
    interval: Optional[float] = Field(default=5, alias=EV_KEYS_INTERVAL)
    verify_ssl: Optional[bool] = Field(alias=EV_KEYS_VERIFY_SSL)
    ssl_ca_cert: Optional[StrictStr] = Field(alias=EV_KEYS_SSL_CA_CERT)
    cert_file: Optional[StrictStr] = Field(alias=EV_KEYS_CERT_FILE)
    key_file: Optional[StrictStr] = Field(alias=EV_KEYS_KEY_FILE)
    assert_hostname: Optional[bool] = Field(alias=EV_KEYS_ASSERT_HOSTNAME)
    connection_pool_maxsize: Optional[int] = Field(
        alias=EV_KEYS_CONNECTION_POOL_MAXSIZE
    )
    archives_root: Optional[StrictStr] = Field(
        default=ctx_paths.CONTEXT_ARCHIVES_ROOT, alias=EV_KEYS_ARCHIVES_ROOT
    )
    header: Optional[Union[StrictStr, PolyaxonServiceHeaders]] = Field(
        alias=EV_KEYS_HEADER
    )
    header_service: Optional[Union[StrictStr, PolyaxonServices]] = Field(
        alias=EV_KEYS_HEADER_SERVICE
    )
    namespace: Optional[StrictStr] = Field(alias=EV_KEYS_K8S_NAMESPACE)
    no_api: Optional[bool] = Field(default=False, alias=EV_KEYS_NO_API)
    disable_errors_reporting: Optional[bool] = Field(
        default=False, alias=EV_KEYS_DISABLE_ERRORS_REPORTING
    )
    compatibility_check_interval: Optional[int] = Field(
        alias=EV_KEYS_INTERVALS_COMPATIBILITY_CHECK
    )
    retries: Optional[int] = Field(alias=EV_KEYS_RETRIES)
    token: Optional[StrictStr]
    client_header: Optional[Dict]

    class Config:
        extra = Extra.ignore

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        use_cloud_host: bool = False,
        retries: Optional[int] = None,
        **data
    ):
        host = (
            clean_host(host or LOCALHOST) if not use_cloud_host else POLYAXON_CLOUD_HOST
        )
        super().__init__(host=host, **data)
        self.retries = retries if not use_cloud_host else 0
        self.token = token
        self.client_header = {}
        if all([self.header, self.header_service]):
            self.client_header["header_name"] = self.header
            self.client_header["header_value"] = self.header_service

    @property
    def base_url(self) -> str:
        return self._BASE_URL.format(clean_host(self.host), self.version)

    def set_cli_header(self) -> None:
        self.header = PolyaxonServiceHeaders.get_header(PolyaxonServiceHeaders.SERVICE)
        self.header_service = VERSION
        self.client_header["header_name"] = self.header
        self.client_header["header_value"] = self.header_service

    def set_agent_header(self) -> None:
        self.header = PolyaxonServiceHeaders.get_header(PolyaxonServiceHeaders.SERVICE)
        self.header_service = PolyaxonServices.AGENT
        self.client_header["header_name"] = self.header
        self.client_header["header_value"] = self.header_service

    def get_full_headers(self, headers=None, auth_key="Authorization") -> Dict:
        request_headers = {}
        request_headers.update(headers or {})
        request_headers.update(self.client_header or {})

        if auth_key not in request_headers and self.token:
            request_headers.update(
                {auth_key: "{} {}".format(self.authentication_type, self.token)}
            )
        if self.header and self.header_service:
            request_headers.update({self.header: self.header_service})
        return request_headers

    @property
    def sdk_config(self) -> Configuration:
        if not self.host and not self.in_cluster:
            raise PolyaxonClientException(
                "Api config requires at least a host if not running in-cluster."
            )

        config = Configuration()
        config.retries = self.retries
        config.debug = self.debug
        config.host = clean_host(self.host)
        config.verify_ssl = self.verify_ssl
        if not config.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        config.ssl_ca_cert = self.ssl_ca_cert
        config.cert_file = self.cert_file
        config.key_file = self.key_file
        config.assert_hostname = self.assert_hostname
        if self.connection_pool_maxsize:
            config.connection_pool_maxsize = self.connection_pool_maxsize
        if self.token:
            config.api_key["ApiKey"] = self.token
            config.api_key_prefix["ApiKey"] = self.authentication_type
        return config

    @property
    def async_sdk_config(self) -> Configuration:
        config = self.sdk_config
        config.connection_pool_maxsize = 100
        return config

    @classmethod
    def patch_from(cls, config: "ClientConfig", **kwargs) -> "ClientConfig":
        data = {**config.to_dict(), **kwargs}
        return cls.from_dict(data)
