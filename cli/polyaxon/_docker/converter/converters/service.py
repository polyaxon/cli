from typing import Dict, Iterable, List, Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._docker import docker_types
from polyaxon._docker.converter.base import BaseConverter
from polyaxon._docker.converter.mixins import ServiceMixin
from polyaxon._flow import V1CompiledOperation, V1Plugins, V1Service


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
    ) -> List[docker_types.V1Container]:
        service = compiled_operation.run  # type: V1Service
        plugins = V1Plugins.get_or_create(
            config=compiled_operation.plugins, auth=default_auth
        )
        kv_env_vars = compiled_operation.get_env_io()
        return self.get_replica_resource(
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
