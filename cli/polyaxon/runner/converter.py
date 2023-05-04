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
from polyaxon.exceptions import PolypodException
from polyaxon.polyflow import V1Init
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
            raise PolypodException(
                "Please make sure that a converter subclass has a valid SPEC_KIND"
            )
        if not self.MAIN_CONTAINER_ID:
            raise PolypodException(
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

    def get_resource(self, **kwargs) -> Dict:
        raise NotImplementedError
