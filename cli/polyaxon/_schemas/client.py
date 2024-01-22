import os

from typing import Dict, Optional, Union

import urllib3

from clipped.compact.pydantic import Extra, Field, StrictStr
from clipped.utils.http import clean_host

from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import (
    ENV_KEYS_API_VERSION,
    ENV_KEYS_ARCHIVES_ROOT,
    ENV_KEYS_ASSERT_HOSTNAME,
    ENV_KEYS_AUTHENTICATION_TYPE,
    ENV_KEYS_CERT_FILE,
    ENV_KEYS_CONNECTION_POOL_MAXSIZE,
    ENV_KEYS_DEBUG,
    ENV_KEYS_DISABLE_ERRORS_REPORTING,
    ENV_KEYS_HEADER,
    ENV_KEYS_HEADER_SERVICE,
    ENV_KEYS_HOST,
    ENV_KEYS_INTERVAL,
    ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK,
    ENV_KEYS_IS_MANAGED,
    ENV_KEYS_IS_OFFLINE,
    ENV_KEYS_K8S_IN_CLUSTER,
    ENV_KEYS_K8S_NAMESPACE,
    ENV_KEYS_KEY_FILE,
    ENV_KEYS_LOG_LEVEL,
    ENV_KEYS_NO_API,
    ENV_KEYS_NO_OP,
    ENV_KEYS_RETRIES,
    ENV_KEYS_SECRET_INTERNAL_TOKEN,
    ENV_KEYS_SSL_CA_CERT,
    ENV_KEYS_TIME_ZONE,
    ENV_KEYS_TIMEOUT,
    ENV_KEYS_TRACKING_TIMEOUT,
    ENV_KEYS_VERIFY_SSL,
    ENV_KEYS_WATCH_INTERVAL,
)
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._sdk.configuration import Configuration
from polyaxon._services.auth import AuthenticationTypes
from polyaxon._services.headers import PolyaxonServiceHeaders
from polyaxon._services.values import PolyaxonServices
from polyaxon.api import LOCALHOST, POLYAXON_CLOUD_HOST
from polyaxon.exceptions import PolyaxonClientException
from polyaxon.pkg import VERSION


class ClientConfig(BaseSchemaModel):
    _IDENTIFIER = "global"

    _PAGE_SIZE = 20
    _BASE_URL = "{}/api/{}"

    host: Optional[StrictStr] = Field(alias=ENV_KEYS_HOST)
    version: Optional[StrictStr] = Field(default="v1", alias=ENV_KEYS_API_VERSION)
    debug: Optional[bool] = Field(default=False, alias=ENV_KEYS_DEBUG)
    log_level: Optional[StrictStr] = Field(alias=ENV_KEYS_LOG_LEVEL)
    authentication_type: Optional[StrictStr] = Field(
        default=AuthenticationTypes.TOKEN, alias=ENV_KEYS_AUTHENTICATION_TYPE
    )
    is_managed: Optional[bool] = Field(default=False, alias=ENV_KEYS_IS_MANAGED)
    is_offline: Optional[bool] = Field(default=False, alias=ENV_KEYS_IS_OFFLINE)
    in_cluster: Optional[bool] = Field(default=False, alias=ENV_KEYS_K8S_IN_CLUSTER)
    no_op: Optional[bool] = Field(default=False, alias=ENV_KEYS_NO_OP)
    timeout: Optional[float] = Field(default=20, alias=ENV_KEYS_TIMEOUT)
    tracking_timeout: Optional[float] = Field(
        default=1, alias=ENV_KEYS_TRACKING_TIMEOUT
    )
    timezone: Optional[StrictStr] = Field(alias=ENV_KEYS_TIME_ZONE)
    watch_interval: Optional[int] = Field(default=5, alias=ENV_KEYS_WATCH_INTERVAL)
    interval: Optional[float] = Field(default=5, alias=ENV_KEYS_INTERVAL)
    verify_ssl: Optional[bool] = Field(alias=ENV_KEYS_VERIFY_SSL)
    ssl_ca_cert: Optional[StrictStr] = Field(alias=ENV_KEYS_SSL_CA_CERT)
    cert_file: Optional[StrictStr] = Field(alias=ENV_KEYS_CERT_FILE)
    key_file: Optional[StrictStr] = Field(alias=ENV_KEYS_KEY_FILE)
    assert_hostname: Optional[bool] = Field(alias=ENV_KEYS_ASSERT_HOSTNAME)
    connection_pool_maxsize: Optional[int] = Field(
        alias=ENV_KEYS_CONNECTION_POOL_MAXSIZE
    )
    archives_root: Optional[StrictStr] = Field(
        default=ctx_paths.CONTEXT_ARCHIVES_ROOT, alias=ENV_KEYS_ARCHIVES_ROOT
    )
    header: Optional[Union[StrictStr, PolyaxonServiceHeaders]] = Field(
        alias=ENV_KEYS_HEADER
    )
    header_service: Optional[Union[StrictStr, PolyaxonServices]] = Field(
        alias=ENV_KEYS_HEADER_SERVICE
    )
    namespace: Optional[StrictStr] = Field(alias=ENV_KEYS_K8S_NAMESPACE)
    no_api: Optional[bool] = Field(default=False, alias=ENV_KEYS_NO_API)
    disable_errors_reporting: Optional[bool] = Field(
        default=False, alias=ENV_KEYS_DISABLE_ERRORS_REPORTING
    )
    compatibility_check_interval: Optional[int] = Field(
        alias=ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK
    )
    retries: Optional[int] = Field(alias=ENV_KEYS_RETRIES)
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

    def get_internal_header(self) -> Dict:
        header = PolyaxonServiceHeaders.get_header(PolyaxonServiceHeaders.INTERNAL)
        return {"header_name": header, "header_value": self.header_service}

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
    def sdk_config(self):
        return self.get_sdk_config()

    @property
    def internal_sdk_config(self):
        return self.get_sdk_config(
            token=os.environ.get(ENV_KEYS_SECRET_INTERNAL_TOKEN),
            authentication_type=AuthenticationTypes.INTERNAL_TOKEN,
        )

    def get_sdk_config(
        self, token: str = None, authentication_type: AuthenticationTypes = None
    ) -> Configuration:
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
            config.api_key["ApiKey"] = token or self.token
            config.api_key_prefix["ApiKey"] = (
                authentication_type or self.authentication_type
            )
        return config

    @property
    def async_sdk_config(self) -> Configuration:
        config = self.sdk_config
        config.connection_pool_maxsize = 100
        return config

    @property
    def async_internal_sdk_config(self) -> Configuration:
        config = self.internal_sdk_config
        config.connection_pool_maxsize = 100
        return config

    @classmethod
    def patch_from(cls, config: "ClientConfig", **kwargs) -> "ClientConfig":
        data = {**config.to_dict(), **kwargs}
        return cls.from_dict(data)
