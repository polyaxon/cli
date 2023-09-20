from typing import Dict

from polyaxon._compiler.contexts.base import BaseContextsManager
from polyaxon._connections import V1Connection
from polyaxon._flow import V1CompiledOperation
from polyaxon._utils.urls_utils import get_proxy_run_url
from polyaxon.api import (
    EXTERNAL_V1_LOCATION,
    REWRITE_EXTERNAL_V1_LOCATION,
    REWRITE_SERVICES_V1_LOCATION,
    SERVICES_V1_LOCATION,
)


class ServiceContextsManager(BaseContextsManager):
    @classmethod
    def resolve(
        cls,
        namespace: str,
        owner_name: str,
        project_name: str,
        run_uuid: str,
        contexts: Dict,
        compiled_operation: V1CompiledOperation,
        connection_by_names: Dict[str, V1Connection],
    ) -> Dict:
        contexts = cls._resolver_replica(
            contexts=contexts,
            init=compiled_operation.run.init,
            connections=compiled_operation.run.connections,
            connection_by_names=connection_by_names,
        )
        if compiled_operation.is_service_run:
            contexts["globals"]["ports"] = compiled_operation.run.ports
            if compiled_operation.run.is_external:
                service = (
                    REWRITE_EXTERNAL_V1_LOCATION
                    if compiled_operation.run.rewrite_path
                    else EXTERNAL_V1_LOCATION
                )
            else:
                service = (
                    REWRITE_SERVICES_V1_LOCATION
                    if compiled_operation.run.rewrite_path
                    else SERVICES_V1_LOCATION
                )
            ports = compiled_operation.run.ports or [80]
            base_urls = []
            for port in ports:
                base_url = get_proxy_run_url(
                    service=service,
                    namespace=namespace,
                    owner=owner_name,
                    project=project_name,
                    run_uuid=run_uuid,
                    port=port,
                )
                base_urls.append(base_url)
            contexts["globals"]["base_url"] = base_urls[0]
            contexts["globals"]["base_urls"] = base_urls
        return contexts
