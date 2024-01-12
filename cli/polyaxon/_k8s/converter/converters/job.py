from typing import Dict, Iterable, Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1CompiledOperation, V1Job, V1Plugins
from polyaxon._k8s.converter.base import BaseConverter
from polyaxon._k8s.converter.mixins import JobMixin
from polyaxon._k8s.custom_resources.job import get_job_custom_resource


class JobConverter(JobMixin, BaseConverter):
    def get_resource(
        self,
        compiled_operation: V1CompiledOperation,
        artifacts_store: V1Connection,
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        default_sa: Optional[str] = None,
        default_auth: bool = False,
    ) -> Dict:
        job = compiled_operation.run  # type: V1Job
        plugins = V1Plugins.get_or_create(
            config=compiled_operation.plugins, auth=default_auth
        )
        kv_env_vars = compiled_operation.get_env_io()
        replica_spec = self.get_replica_resource(
            plugins=plugins,
            environment=job.environment,
            volumes=job.volumes,
            init=job.init,
            sidecars=job.sidecars,
            container=job.container,
            artifacts_store=artifacts_store,
            connections=job.connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            kv_env_vars=kv_env_vars,
            default_sa=default_sa,
        )
        return get_job_custom_resource(
            namespace=compiled_operation.namespace or self.namespace,
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
        )
