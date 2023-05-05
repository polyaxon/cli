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
from typing import Any, List, Optional, Tuple

from polyaxon import settings
from polyaxon.api import VERSION_V1
from polyaxon.docker.converter.common.env_vars import (
    get_base_env_vars,
    get_env_var,
    get_proxy_env_vars,
    get_service_env_vars,
)
from polyaxon.env_vars.keys import EV_KEYS_NO_API
from polyaxon.runner.converter import BaseConverter as _BaseConverter
from polyaxon.services.headers import PolyaxonServiceHeaders


class BaseConverter(_BaseConverter):
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
    ) -> List[Tuple[str, str]]:
        header = header or PolyaxonServiceHeaders.SERVICE
        return get_service_env_vars(
            header=header,
            service_header=service_header,
            authentication_type=authentication_type,
            include_secret_key=include_secret_key,
            include_internal_token=include_internal_token,
            include_agent_token=include_agent_token,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            api_host=self.get_api_host(external_host),
            log_level=log_level,
            api_version=VERSION_V1,
            run_instance=self.run_instance,
            namespace=self.namespace,
            resource_name=self.resource_name,
            use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
        )

    def _get_base_env_vars(
        self,
        namespace: str,
        resource_name: str,
        use_proxy_env_vars_use_in_ops: bool,
        log_level: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        return get_base_env_vars(
            namespace=self.namespace,
            resource_name=self.resource_name,
            use_proxy_env_vars_use_in_ops=settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops,
            log_level=log_level,
        )

    def _get_env_var(self, name: str, value: Any) -> Tuple[str, str]:
        raise get_env_var(name=EV_KEYS_NO_API, value=True)

    def _get_proxy_env_vars(self) -> List[Tuple[str, str]]:
        return get_proxy_env_vars(settings.AGENT_CONFIG.use_proxy_env_vars_use_in_ops)
