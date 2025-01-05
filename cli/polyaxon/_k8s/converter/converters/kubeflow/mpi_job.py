from typing import Dict, Iterable, Optional

from polyaxon import pkg
from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1CompiledOperation, V1KFReplica, V1MPIJob, V1Plugins
from polyaxon._k8s.converter.base import BaseConverter
from polyaxon._k8s.converter.mixins import MPIJobMixin
from polyaxon._k8s.custom_resources.kubeflow import get_mpi_job_custom_resource
from polyaxon._k8s.replica import ReplicaSpec


class MPIJobConverter(MPIJobMixin, BaseConverter):
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
        job: V1MPIJob = compiled_operation.run

        def _get_replica(replica: Optional[V1KFReplica]) -> Optional[ReplicaSpec]:
            if not replica:
                return None
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
            )

        kv_env_vars = compiled_operation.get_env_io()
        plugins = V1Plugins.get_or_create(
            config=compiled_operation.plugins, auth=default_auth
        )
        launcher = _get_replica(job.launcher)
        worker = _get_replica(job.worker)
        labels = self.get_labels(version=pkg.VERSION, labels={})

        return get_mpi_job_custom_resource(
            namespace=self.namespace,
            resource_name=self.resource_name,
            launcher=launcher,
            worker=worker,
            clean_pod_policy=job.clean_pod_policy,
            scheduling_policy=job.scheduling_policy,
            slots_per_worker=job.slots_per_worker,
            termination=compiled_operation.termination,
            collect_logs=plugins.collect_logs,
            sync_statuses=plugins.sync_statuses,
            notifications=plugins.notifications,
            labels=labels,
            annotations=self.annotations,
        )
