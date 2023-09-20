import copy

from typing import Dict, Iterable, List, Optional

from clipped.utils.sanitizers import sanitize_string_dict
from clipped.utils.strings import slugify

from polyaxon import pkg, settings
from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1Environment, V1Init, V1Plugins
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.base.containers import ContainerMixin
from polyaxon._k8s.converter.base.env_vars import EnvMixin
from polyaxon._k8s.converter.base.init import InitConverter
from polyaxon._k8s.converter.base.main import MainConverter
from polyaxon._k8s.converter.base.mounts import MountsMixin
from polyaxon._k8s.converter.base.sidecar import SidecarConverter
from polyaxon._k8s.converter.common.annotations import get_connection_annotations
from polyaxon._k8s.converter.pod.volumes import get_pod_volumes
from polyaxon._k8s.replica import ReplicaSpec
from polyaxon._runner.converter import BaseConverter as _BaseConverter
from polyaxon._runner.kinds import RunnerKind
from polyaxon.exceptions import PolyaxonConverterError


class BaseConverter(
    MainConverter,
    InitConverter,
    SidecarConverter,
    ContainerMixin,
    EnvMixin,
    MountsMixin,
    _BaseConverter,
):
    RUNNER_KIND = RunnerKind.K8S
    GROUP: Optional[str] = None
    API_VERSION: Optional[str] = None
    PLURAL: Optional[str] = None
    K8S_ANNOTATIONS_KIND: Optional[str] = None
    K8S_LABELS_COMPONENT: Optional[str] = None
    K8S_LABELS_PART_OF: Optional[str] = None

    def is_valid(self):
        super().is_valid()
        if not self.GROUP:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid GROUP"
            )
        if not self.API_VERSION:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid API_VERSION"
            )
        if not self.PLURAL:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid PLURAL"
            )
        if not self.K8S_ANNOTATIONS_KIND:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid K8S_ANNOTATIONS_KIND"
            )
        if not self.K8S_LABELS_COMPONENT:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid K8S_LABELS_COMPONENT"
            )
        if not self.K8S_LABELS_PART_OF:
            raise PolyaxonConverterError(
                "Please make sure that a converter subclass has a valid K8S_LABELS_PART_OF"
            )

    def get_recommended_labels(self, version: str) -> Dict:
        return {
            "app.kubernetes.io/name": slugify(
                self.run_name[:63] if self.run_name else self.run_name
            ),
            "app.kubernetes.io/instance": self.run_uuid,
            "app.kubernetes.io/version": version,
            "app.kubernetes.io/part-of": self.K8S_LABELS_PART_OF,
            "app.kubernetes.io/component": self.K8S_LABELS_COMPONENT,
            "app.kubernetes.io/managed-by": "polyaxon",
        }

    @property
    def annotations(self) -> Dict:
        return {
            "operation.polyaxon.com/name": self.run_name,
            "operation.polyaxon.com/owner": self.owner_name,
            "operation.polyaxon.com/project": self.project_name,
            "operation.polyaxon.com/kind": self.K8S_ANNOTATIONS_KIND,
        }

    def get_annotations(
        self,
        annotations: Dict,
        artifacts_store: Optional[V1Connection],
        init_connections: Optional[List[V1Init]],
        connections: List[str],
        connection_by_names: Optional[Dict[str, V1Connection]],
    ) -> Dict:
        annotations = annotations or {}
        annotations = copy.copy(annotations)
        connections_annotations = get_connection_annotations(
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connections=connections,
            connection_by_names=connection_by_names,
        )
        connections_annotations = connections_annotations or {}
        annotations.update(connections_annotations)
        annotations.update(self.annotations)
        return sanitize_string_dict(annotations)

    def get_labels(self, version: str, labels: Dict) -> Dict:
        labels = labels or {}
        labels = copy.copy(labels)
        labels.update(self.get_recommended_labels(version=version))
        return sanitize_string_dict(labels)

    @staticmethod
    def _new_container(name: str) -> k8s_schemas.V1Container:
        return k8s_schemas.V1Container(name=name)

    @classmethod
    def _ensure_container(
        cls, container: k8s_schemas, volumes: List[k8s_schemas.V1Volume]
    ) -> k8s_schemas.V1Container:
        return container

    def get_replica_resource(
        self,
        environment: V1Environment,
        plugins: V1Plugins,
        volumes: List[k8s_schemas.V1Volume],
        init: List[V1Init],
        sidecars: List[k8s_schemas.V1Container],
        container: k8s_schemas.V1Container,
        artifacts_store: V1Connection,
        connections: List[str],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        kv_env_vars: List[List],
        default_sa: Optional[str] = None,
        ports: List[int] = None,
        num_replicas: Optional[int] = None,
        custom: Dict = None,
    ) -> ReplicaSpec:
        volumes = volumes or []
        init = init or []
        sidecars = sidecars or []
        connections = connections or []
        environment = environment or V1Environment()
        environment.service_account_name = (
            environment.service_account_name
            or default_sa
            or settings.AGENT_CONFIG.runs_sa
        )

        init_connections = self.filter_connections_from_init(init=init)

        volumes = get_pod_volumes(
            plugins=plugins,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            connections=connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            volumes=volumes,
        )

        init_containers = self.get_init_containers(
            polyaxon_init=self.polyaxon_init,
            plugins=plugins,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            init_containers=self.filter_containers_from_init(init=init),
            connection_by_names=connection_by_names,
            log_level=plugins.log_level,
        )

        sidecar_containers = self.get_sidecar_containers(
            polyaxon_sidecar=self.polyaxon_sidecar,
            plugins=plugins,
            artifacts_store=artifacts_store,
            sidecar_containers=sidecars,
            log_level=plugins.log_level,
        )

        main_container = self.get_main_container(
            main_container=container,
            plugins=plugins,
            artifacts_store=artifacts_store,
            connections=connections,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            ports=ports,
            kv_env_vars=kv_env_vars,
        )

        labels = self.get_labels(version=pkg.VERSION, labels=environment.labels)
        annotations = self.get_annotations(
            annotations=environment.annotations,
            artifacts_store=artifacts_store,
            connections=connections,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
        )
        return ReplicaSpec(
            volumes=volumes,
            init_containers=[self._sanitize_container(c) for c in init_containers],
            sidecar_containers=[
                self._sanitize_container(c) for c in sidecar_containers
            ],
            main_container=main_container,
            labels=labels,
            annotations=annotations,
            environment=environment,
            num_replicas=num_replicas,
            custom=custom,
        )
