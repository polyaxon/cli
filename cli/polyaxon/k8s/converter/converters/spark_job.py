from typing import Dict, Iterable, Optional

from polyaxon import pkg
from polyaxon.connections import V1Connection, V1ConnectionResource
from polyaxon.k8s.converter.base import BaseConverter
from polyaxon.k8s.converter.mixins import SparkJobMixin
from polyaxon.k8s.custom_resources.spark_job import get_spark_job_custom_resource
from polyaxon.k8s.replica import ReplicaSpec
from polyaxon.polyflow import V1CompiledOperation, V1Plugins, V1SparkJob, V1SparkReplica


class SparkJobConverter(SparkJobMixin, BaseConverter):
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
        job = compiled_operation.run  # type: V1SparkJob

        def _get_replica(replica: Optional[V1SparkReplica]) -> Optional[ReplicaSpec]:
            if not replica:
                return None
            return self.get_replica_resource(
                plugins=plugins,
                environment=replica.environment,
                volumes=job.volumes or [],
                init=replica.init or [],
                sidecars=replica.sidecars or [],
                container=replica.container,
                artifacts_store=artifacts_store,
                connections=job.connections or [],
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
        executor = _get_replica(job.executor)
        driver = _get_replica(job.driver)
        labels = self.get_labels(version=pkg.VERSION, labels={})

        return get_spark_job_custom_resource(
            namespace=self.namespace,
            resource_name=self.resource_name,
            executor=executor,
            driver=driver,
            termination=compiled_operation.termination,
            collect_logs=plugins.collect_logs,
            sync_statuses=plugins.sync_statuses,
            notifications=plugins.notifications,
            labels=labels,
            annotations=self.annotations,
        )
