from typing import Dict, Iterable, List, Optional

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._docker import docker_types
from polyaxon._docker.converter.base import BaseConverter
from polyaxon._flow import V1CompiledOperation, V1Job, V1Plugins
from polyaxon._k8s.converter.mixins import JobMixin


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
    ) -> List[docker_types.V1Container]:
        job: V1Job = compiled_operation.run
        plugins = V1Plugins.get_or_create(
            config=compiled_operation.plugins, auth=default_auth
        )
        kv_env_vars = compiled_operation.get_env_io()
        return self.get_replica_resource(
            environment=job.environment,
            plugins=plugins,
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
