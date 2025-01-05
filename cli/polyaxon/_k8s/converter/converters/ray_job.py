from typing import Dict, Iterable, Optional

from clipped.utils.json import orjson_dumps

from polyaxon import pkg
from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1CompiledOperation, V1Plugins, V1RayJob, V1RayReplica
from polyaxon._k8s.converter.base import BaseConverter
from polyaxon._k8s.converter.mixins import RayJobMixin
from polyaxon._k8s.custom_resources.ray_job import get_ray_job_custom_resource
from polyaxon._k8s.replica import ReplicaSpec


class RayJobConverter(RayJobMixin, BaseConverter):
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
        job: V1RayJob = compiled_operation.run

        def _get_replica(replica: Optional[V1RayReplica]) -> Optional[ReplicaSpec]:
            if not replica:
                return None
            custom = {}
            if replica.min_replicas:
                custom["min_replicas"] = replica.min_replicas
            if replica.max_replicas:
                custom["max_replicas"] = replica.max_replicas
            if replica.ray_start_params:
                custom["ray_start_params"] = replica.ray_start_params
            return self.get_replica_resource(
                plugins=plugins,
                environment=replica.environment,
                volumes=replica.volumes or [],
                init=replica.init or [],
                sidecars=replica.sidecars or [],
                container=replica.container,
                artifacts_store=artifacts_store,
                connections=replica.connections or [],
                connection_by_names=connection_by_names,
                secrets=secrets,
                config_maps=config_maps,
                kv_env_vars=kv_env_vars,
                default_sa=default_sa,
                num_replicas=replica.replicas,
                custom=custom,
            )

        kv_env_vars = compiled_operation.get_env_io()
        plugins = V1Plugins.get_or_create(
            config=compiled_operation.plugins, auth=default_auth
        )
        head = _get_replica(job.head)
        workers = None
        if job.workers:
            workers = {n: _get_replica(w) for n, w in job.workers.items()}
        labels = self.get_labels(version=pkg.VERSION, labels={})

        return get_ray_job_custom_resource(
            namespace=self.namespace,
            resource_name=self.resource_name,
            head=head,
            workers=workers,
            entrypoint=job.entrypoint,
            metadata=job.metadata,
            runtime_env=orjson_dumps(job.runtime_env),
            ray_version=job.ray_version,
            termination=compiled_operation.termination,
            collect_logs=plugins.collect_logs,
            sync_statuses=plugins.sync_statuses,
            notifications=plugins.notifications,
            labels=labels,
            annotations=self.annotations,
        )
