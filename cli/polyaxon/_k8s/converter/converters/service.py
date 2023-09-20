from typing import Dict, Iterable, Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1CompiledOperation, V1Plugins, V1Service
from polyaxon._k8s.converter.base import BaseConverter
from polyaxon._k8s.converter.mixins import ServiceMixin
from polyaxon._k8s.custom_resources.service import get_service_custom_resource


class ServiceConverter(ServiceMixin, BaseConverter):
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
