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
from polyaxon.k8s.custom_resources.job import get_job_custom_resource
from polyaxon.polyflow import V1CompiledOperation, V1Job, V1Plugins
from polyaxon.polypod.compiler.converters.base import (
    BaseConverter,
    PlatformConverterMixin,
)
from polyaxon.polypod.mixins import JobMixin
from polyaxon.polypod.specs.contexts import PluginsContextsSpec


class JobConverter(JobMixin, BaseConverter):
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
        job = compiled_operation.run  # type: V1Job
        plugins = compiled_operation.plugins or V1Plugins()
        contexts = PluginsContextsSpec.from_config(plugins, default_auth=default_auth)
        kv_env_vars = compiled_operation.get_env_io()
        replica_spec = self.get_replica_resource(
            plugins=plugins,
            contexts=contexts,
            environment=job.environment,
            volumes=job.volumes or [],
            init=job.init or [],
            sidecars=job.sidecars or [],
            container=job.container,
            artifacts_store=artifacts_store,
            connections=job.connections or [],
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            kv_env_vars=kv_env_vars,
            default_sa=default_sa,
        )
        return get_job_custom_resource(
            namespace=self.namespace,
            main_container=replica_spec.main_container,
            sidecar_containers=replica_spec.sidecar_containers,
            init_containers=replica_spec.init_containers,
            resource_name=self.resource_name,
            volumes=replica_spec.volumes,
            environment=replica_spec.environment,
            termination=compiled_operation.termination,
            collect_logs=contexts.collect_logs,
            sync_statuses=contexts.sync_statuses,
            notifications=plugins.notifications,
            labels=replica_spec.labels,
            annotations=replica_spec.annotations,
        )


class PlatformJobConverter(PlatformConverterMixin, JobConverter):
    pass
