import os

from polyaxon import settings
from polyaxon.api import VERSION_V1
from polyaxon.docker.converter.base import BaseConverter
from polyaxon.env_vars.keys import EV_KEYS_PLATFORM_HOST
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.services.headers import PolyaxonServiceHeaders
from polyaxon.services.values import PolyaxonServices
from polyaxon.utils.test_utils import BaseTestCase


class DummyConverter(BaseConverter):
    SPEC_KIND = "dummy"
    MAIN_CONTAINER_ID = "dummy"

    def get_main_env_vars(self, external_host: bool = False, **kwargs):
        pass

    def get_resource(self, **kwargs):
        pass


class TestBaseConverter(BaseTestCase):
    SET_AGENT_SETTINGS = True

    def setUp(self):
        super().setUp()
        settings.AGENT_CONFIG.app_secret_name = "polyaxon"
        settings.AGENT_CONFIG.agent_secret_name = "agent"
        settings.CLIENT_CONFIG.host = "https://polyaxon.com"
        self.converter = DummyConverter(
            owner_name="owner-name",
            project_name="project-name",
            run_name="run-name",
            run_uuid="run_uuid",
        )

    def test_k8s_to_docker_env_var(self):
        values = [
            {"name": "bar", "value": "foo"},
            k8s_schemas.V1EnvVar(name="foo", value="bar"),
        ]
        expected = [{"foo": "bar"}, {"foo": "bar"}]
        self.converter._k8s_to_docker_env_var(values) == expected

    def test_k8s_to_docker_volume_mounts(self):
        volume_mounts = [
            k8s_schemas.V1VolumeMount(name="a", mount_path="bar", read_only=True),
            k8s_schemas.V1VolumeMount(name="b", mount_path="bar"),
        ]
        volumes = [
            k8s_schemas.V1Volume(
                name="q",
                persistent_volume_claim=k8s_schemas.V1PersistentVolumeClaimVolumeSource(
                    claim_name="bar"
                ),
            ),
            k8s_schemas.V1Volume(
                name="b", host_path=k8s_schemas.V1HostPathVolumeSource(path="bar")
            ),
        ]
        expected = [{"foo": "bar"}, {"foo": "bar"}]
        self.converter._k8s_to_docker_volume_mounts(
            volume_mounts=volume_mounts, volumes=volumes
        ) == expected

    def test_get_service_env_vars(self):
        # Call with default
        env_vars = self.converter._get_service_env_vars(service_header=None)
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=None,
            log_level=None,
            authentication_type=None,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=False,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )

        self.converter.internal_auth = True
        env_vars = self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            include_secret_key=True,
            include_internal_token=True,
            include_agent_token=False,
            authentication_type="internal",
        )
        assert env_vars == self.converter._get_service_env_vars(
            header="header-foo",
            service_header="sa-foo",
            authentication_type="internal",
            include_secret_key=True,
            include_internal_token=True,
            include_agent_token=False,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )

        self.converter.internal_auth = False
        env_vars = self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            authentication_type="internal",
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
        )
        assert env_vars == self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            authentication_type="internal",
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        env_vars = self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            authentication_type="internal",
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            external_host=True,
        )
        # Default platform host
        assert env_vars == self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            authentication_type="internal",
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=True,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        # Setting an env var for the EV_KEYS_PLATFORM_HOST and LOG_LEVEL
        current = os.environ.get(EV_KEYS_PLATFORM_HOST)
        os.environ[EV_KEYS_PLATFORM_HOST] = "foo"
        env_vars = self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            authentication_type="internal",
            log_level="info",
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            external_host=True,
        )
        assert env_vars == self.converter._get_service_env_vars(
            service_header="sa-foo",
            header="header-foo",
            authentication_type="internal",
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            log_level="info",
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=True,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        if current:
            os.environ[EV_KEYS_PLATFORM_HOST] = current
        else:
            del os.environ[EV_KEYS_PLATFORM_HOST]

        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_service_env_vars(
                service_header="sa-foo",
                header="header-foo",
                include_secret_key=False,
                include_internal_token=True,
                include_agent_token=True,
                authentication_type="internal",
                log_level="info",
            )

    def test_get_auth_service_env_vars(self):
        self.converter.internal_auth = True
        env_vars = self.converter._get_auth_service_env_vars()
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.INTERNAL,
            service_header=PolyaxonServices.INITIALIZER,
            authentication_type=AuthenticationTypes.INTERNAL_TOKEN,
            include_secret_key=False,
            include_internal_token=True,
            include_agent_token=False,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )

        self.converter.internal_auth = False
        env_vars = self.converter._get_auth_service_env_vars(log_level="info")
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.INITIALIZER,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            log_level="info",
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        env_vars = self.converter._get_auth_service_env_vars(external_host=True)
        # Default platform host
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.INITIALIZER,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        # Setting an env var for the EV_KEYS_PLATFORM_HOST
        current = os.environ.get(EV_KEYS_PLATFORM_HOST)
        os.environ[EV_KEYS_PLATFORM_HOST] = "foo"
        env_vars = self.converter._get_auth_service_env_vars(external_host=True)
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.INITIALIZER,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=True,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=True,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        if current:
            os.environ[EV_KEYS_PLATFORM_HOST] = current
        else:
            del os.environ[EV_KEYS_PLATFORM_HOST]

    def test_get_polyaxon_sidecar_service_env_vars(self):
        self.converter.internal_auth = True
        env_vars = self.converter._get_polyaxon_sidecar_service_env_vars()
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.SIDECAR,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=False,
            log_level=None,
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )

        self.converter.internal_auth = False
        env_vars = self.converter._get_polyaxon_sidecar_service_env_vars(
            log_level="info"
        )
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.SIDECAR,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=False,
            log_level="info",
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=False,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        env_vars = self.converter._get_polyaxon_sidecar_service_env_vars(
            external_host=True, log_level="debug"
        )
        # Default platform host
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.SIDECAR,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=False,
            log_level="debug",
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=True,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        # Setting an env var for the EV_KEYS_PLATFORM_HOST
        current = os.environ.get(EV_KEYS_PLATFORM_HOST)
        os.environ[EV_KEYS_PLATFORM_HOST] = "foo"
        env_vars = self.converter._get_polyaxon_sidecar_service_env_vars(
            external_host=True,
            log_level="debug",
        )
        assert env_vars == self.converter._get_service_env_vars(
            header=PolyaxonServiceHeaders.SERVICE,
            service_header=PolyaxonServices.SIDECAR,
            authentication_type=AuthenticationTypes.TOKEN,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=False,
            log_level="debug",
            polyaxon_default_secret_ref=settings.AGENT_CONFIG.app_secret_name,
            polyaxon_agent_secret_ref=settings.AGENT_CONFIG.agent_secret_name,
            external_host=True,
            api_version=VERSION_V1,
            use_proxy_env_vars_use_in_ops=False,
        )
        if current:
            os.environ[EV_KEYS_PLATFORM_HOST] = current
        else:
            del os.environ[EV_KEYS_PLATFORM_HOST]
