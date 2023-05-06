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

from typing import Any, Dict, List, Optional

from clipped.utils.http import clean_host

from polyaxon import settings
from polyaxon.env_vars.keys import EV_KEYS_LOG_LEVEL, EV_KEYS_NO_API
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.polyflow import V1Init
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.services.headers import PolyaxonServiceHeaders
from polyaxon.services.values import PolyaxonServices
from polyaxon.utils.fqn_utils import get_resource_name, get_run_instance
from polyaxon.utils.host_utils import get_api_host


class BaseConverter:
    SPEC_KIND = None
    MAIN_CONTAINER_ID = None

    def __init__(
        self,
        owner_name: str,
        project_name: str,
        run_name: str,
        run_uuid: str,
        run_path: Optional[str] = None,
        namespace: str = "default",
        internal_auth: bool = False,
        base_env_vars: bool = False,
    ):
        self.is_valid()
        self.owner_name = owner_name
        self.project_name = project_name
        self.run_name = run_name
        self.run_uuid = run_uuid
        self.run_path = run_path or self.run_uuid
        self.resource_name = self.get_resource_name()
        self.run_instance = self.get_instance()
        self.namespace = namespace
        self.internal_auth = internal_auth
        self.base_env_vars = base_env_vars

    def get_instance(self):
        return get_run_instance(
            owner=self.owner_name, project=self.project_name, run_uuid=self.run_uuid
        )

    def get_resource_name(self):
        return get_resource_name(self.run_uuid)

    def is_valid(self):
        if not self.SPEC_KIND:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid SPEC_KIND"
            )
        if not self.MAIN_CONTAINER_ID:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid MAIN_CONTAINER_ID"
            )

    @staticmethod
    def get_by_name(values: List[Any]):
        return {c.name: c for c in values}

    def get_api_host(self, external_host: bool = False):
        if external_host:
            return get_api_host(default=settings.CLIENT_CONFIG.host)
        else:
            return clean_host(settings.CLIENT_CONFIG.host)

    def filter_connections_from_init(self, init: List[V1Init]) -> List[V1Init]:
        return [i for i in init if i.has_connection()]

    def _get_service_env_vars(
        self,
        service_header: str,
        header: Optional[str] = None,
        include_secret_key: bool = False,
        include_internal_token: bool = False,
        include_agent_token: bool = False,
        authentication_type: Optional[str] = None,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> List[Any]:
        raise NotImplementedError

    def _get_base_env_vars(
        self,
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str] = None,
    ) -> List[Any]:
        raise NotImplementedError

    def _get_env_var(self, name: str, value: Any) -> Any:
        raise NotImplementedError

    def _get_proxy_env_vars(self) -> List[Any]:
        raise NotImplementedError

    def get_main_env_vars(
        self, external_host: bool = False, log_level: Optional[str] = None, **kwargs
    ) -> Optional[Any]:
        if self.base_env_vars:
            return self._get_base_env_vars(
                namespace=self.namespace,
                resource_name=self.resource_name,
                use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
                log_level=log_level,
            )
        return self._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=external_host,
            log_level=log_level,
        )

    def get_polyaxon_sidecar_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[Any]]:
        if not self.base_env_vars:
            return self._get_service_env_vars(
                service_header=PolyaxonServices.SIDECAR,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env += [self._get_env_var(name=EV_KEYS_NO_API, value=True)]
        if log_level:
            env += [self._get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level)]
        proxy_env = self._get_proxy_env_vars()
        if proxy_env:
            env += proxy_env
        return env

    def get_auth_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[Any]]:
        if self.base_env_vars:
            return None
        return self._get_service_env_vars(
            service_header=PolyaxonServices.INITIALIZER,
            include_internal_token=self.internal_auth,
            include_agent_token=not self.internal_auth,
            authentication_type=(
                AuthenticationTypes.INTERNAL_TOKEN
                if self.internal_auth
                else AuthenticationTypes.TOKEN
            ),
            header=(
                PolyaxonServiceHeaders.INTERNAL
                if self.internal_auth
                else PolyaxonServiceHeaders.SERVICE
            ),
            external_host=external_host,
            log_level=log_level,
        )

    def get_init_service_env_vars(
        self,
        external_host: bool = False,
        log_level: Optional[str] = None,
    ) -> Optional[List[Any]]:
        if not self.base_env_vars:
            return self._get_service_env_vars(
                service_header=PolyaxonServices.INITIALIZER,
                authentication_type=AuthenticationTypes.TOKEN,
                header=PolyaxonServiceHeaders.SERVICE,
                external_host=external_host,
                log_level=log_level,
            )
        env = []
        if settings.CLIENT_CONFIG.no_api:
            env.append(self._get_env_var(name=EV_KEYS_NO_API, value=True))
        if log_level:
            env.append(self._get_env_var(name=EV_KEYS_LOG_LEVEL, value=log_level))
        proxy_env = self._get_proxy_env_vars()
        if proxy_env:
            env += proxy_env
        return env

    def get_resource(self, **kwargs) -> Any:
        raise NotImplementedError
