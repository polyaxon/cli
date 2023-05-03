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

from typing import Dict, Iterable, Optional

from polyaxon.connections import V1Connection, V1K8sResource
from polyaxon.k8s.custom_resources.service import get_service_custom_resource
from polyaxon.polyflow import V1CompiledOperation, V1Plugins, V1Service
from polyaxon.converter.converters.base import (
    BaseConverter,
    PlatformConverterMixin,
)
from polyaxon.converter.mixins import ServiceMixin


class ServiceConverter(ServiceMixin, BaseConverter):
    def get_resource(
        self,
        compiled_operation: V1CompiledOperation,
        artifacts_store: V1Connection,
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1K8sResource]],
        config_maps: Optional[Iterable[V1K8sResource]],
        default_sa: Optional[str] = None,
        default_auth: bool = False,
    ) -> Dict:
        service = compiled_operation.run  # type: V1Service
        plugins = V1Plugins.get_or_create(
            config=compiled_operation.plugins, auth=default_auth
        )
        kv_env_vars = compiled_operation.get_env_io()
        replica_spec = self.get_replica_resource(
            plugins=plugins,
            environment=service.environment,
            volumes=service.volumes,
            init=service.init,
            sidecars=service.sidecars,
            container=service.container,
            artifacts_store=artifacts_store,
            connections=service.connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            kv_env_vars=kv_env_vars,
            default_sa=default_sa,
            ports=service.ports,
        )
        return get_service_custom_resource(
            namespace=self.namespace,
            main_container=replica_spec.main_container,
            sidecar_containers=replica_spec.sidecar_containers,
            init_containers=replica_spec.init_containers,
            resource_name=self.resource_name,
            volumes=replica_spec.volumes,
            environment=replica_spec.environment,
            termination=compiled_operation.termination,
            collect_logs=plugins.collect_logs,
            sync_statuses=plugins.sync_statuses,
            notifications=plugins.notifications,
            labels=replica_spec.labels,
            annotations=replica_spec.annotations,
            ports=service.ports,
            is_external=service.is_external,
            replicas=service.replicas,
        )


class PlatformServiceConverter(PlatformConverterMixin, ServiceConverter):
    pass