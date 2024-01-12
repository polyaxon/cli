from clipped.compact.pydantic import ValidationError

from polyaxon._deploy import reader
from polyaxon._deploy.schemas.deployment import DeploymentConfig
from polyaxon._deploy.schemas.service_types import ServiceTypes
from polyaxon._utils.test_utils import BaseTestCase


class TestDeploymentConfig(BaseTestCase):
    def test_read_deploy_config_values1(self):
        config = reader.read("tests/fixtures/deployment/values1.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress.enabled is True
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector is None
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.scheduler is None
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.postgresql.enabled is False
        assert config.rabbitmq is None
        assert config.email is None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "azure"
        assert config.artifacts_store.kind == "wasb"
        assert config.artifacts_store.secret.to_dict() == {"name": "az-secret"}
        assert config.connections is None
        assert config.ldap is None

    def test_read_deploy_config_values2(self):
        config = reader.read("tests/fixtures/deployment/values2.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.deployment_type is None
        assert config.namespace is None
        assert config.rbac.enabled is False
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress.enabled is False
        assert config.gateway.service.type == ServiceTypes.NODE_PORT
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector == {"polyaxon": "core"}
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.gateway.replicas == 3
        assert config.organization_key is None
        assert config.scheduler.replicas == 3
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.postgresql.persistence is not None
        assert config.rabbitmq is None
        assert config.email is not None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "azure"
        assert config.artifacts_store.kind == "wasb"
        assert config.artifacts_store.secret.to_dict() == {"name": "az-secret"}
        assert len(config.connections) == 5
        assert config.ldap is None

    def test_read_deploy_config_values3(self):
        config = reader.read("tests/fixtures/deployment/values3.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.deployment_type is None
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress.enabled is True
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector == {"polyaxon": "core"}
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.gateway.replicas == 3
        assert config.scheduler.replicas == 3
        assert config.worker.replicas == 3
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.postgresql.enabled is True
        assert config.rabbitmq.enabled is False
        assert config.redis.enabled is False
        assert config.email is not None
        assert config.host_name == "123.123.123.123"
        assert config.allowed_hosts == ["foo.bar.com", "123.123.12.3"]
        assert config.intervals is None
        assert config.artifacts_store.name == "store"
        assert config.artifacts_store.kind == "host_path"
        assert config.artifacts_store.schema_.mount_path == "/tmp/outputs"
        assert len(config.connections) == 2
        assert config.ldap is None
        assert config.ssl is None
        assert config.dns is None

    def test_read_deploy_config_values4(self):
        config = reader.read("tests/fixtures/deployment/values4.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.deployment_type is None
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.timezone == "Europe/Berlin"
        assert config.environment == "staging"
        assert config.ingress.enabled is True
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.gateway.concurrency == 2
        assert config.gateway.per_core is True
        assert config.user.to_dict() == {"password": "test"}
        assert config.node_selector == {"polyaxon": "core"}
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.gateway.replicas == 1
        assert config.scheduler.replicas == 1
        assert config.worker.replicas == 1
        assert config.beat.image_tag == "latest"
        assert config.worker.image_tag == "latest"
        assert config.api_hooks.image_tag == "latest"
        assert config.api_hooks.load_fixtures is True
        assert config.api_hooks.admin_user is False
        assert config.api_hooks.tables is False
        assert config.api_hooks.sync_db is False
        assert config.clean_hooks is None
        assert config.postgresql is None
        assert config.rabbitmq is None
        assert config.broker is None
        assert config.email is None
        assert config.host_name == "19.3.50.12"
        assert config.allowed_hosts == ["127.0.0.1", "123.123.12.3"]
        assert config.intervals is None
        assert config.artifacts_store.name == "test"
        assert config.artifacts_store.kind == "volume_claim"
        assert config.artifacts_store.schema_.volume_claim == "test"
        assert len(config.connections) == 2
        assert config.auth.enabled is False
        assert config.auth.external is None
        assert config.auth.use_resolver is True
        assert config.ui.enabled is True
        assert config.ui.offline is True
        assert config.ui.static_url == "https://ffo.com"
        assert config.ui.admin_enabled is True
        assert config.ldap is not None
        assert config.ssl.enabled is True
        assert config.ssl.secret_name == "polyaxon-cert"
        assert config.ssl.path == "/etc/tls"
        assert config.dns == {
            "backend": "coredns",
            "customCluster": "custom.cluster.name",
            "prefix": None,
        }
        assert config.security_context is not None
        assert config.security_context.enabled is True
        assert config.security_context.run_as_user == 2222
        assert config.security_context.run_as_group == 2222
        assert config.security_context.fs_group == 2222
        assert config.security_context.allow_privilege_escalation is False
        assert config.security_context.run_as_non_root is True
        assert config.security_context.fs_group_change_policy == "Always"
        assert config.password_length == 4

    def test_read_deploy_config_values5(self):
        config = reader.read("tests/fixtures/deployment/values5.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.deployment_type is None
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone == "Europe/Berlin"
        assert config.environment == "staging"
        assert config.ingress.enabled is True
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "test"}
        assert config.node_selector == {"polyaxon": "core"}
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.gateway.replicas == 1
        assert config.organization_key == "some-key"
        assert config.scheduler.replicas == 1
        assert config.scheduler.celery.to_dict() == {
            "taskTrackStarted": False,
            "brokerPoolLimit": 2,
            "confirmPublish": False,
            "workerPrefetchMultiplier": 2,
            "workerMaxTasksPerChild": 2,
            "workerMaxMemoryPerChild": 2,
            "taskAlwaysEager": True,
        }
        assert config.worker.replicas == 1
        assert config.worker.celery.to_dict() == {
            "taskTrackStarted": True,
            "brokerPoolLimit": 4,
            "confirmPublish": True,
            "workerPrefetchMultiplier": 4,
            "workerMaxTasksPerChild": 4,
            "workerMaxMemoryPerChild": 4,
        }
        assert config.beat.image_tag == "latest"
        assert config.api_hooks.image_tag == "latest"
        assert config.api_hooks.image_pull_policy == "Always"
        assert config.api_hooks.load_fixtures is True
        assert config.api_hooks.admin_user is True
        assert config.api_hooks.tables is True
        assert config.api_hooks.sync_db is True
        assert config.clean_hooks.image_tag == "latest"
        assert config.clean_hooks.image_pull_policy == "Always"
        assert config.postgresql is None
        assert config.rabbitmq.enabled is False
        assert config.broker == "redis"
        assert config.email is None
        assert config.host_name == "19.3.50.12"
        assert config.allowed_hosts == ["127.0.0.1", "123.123.12.3"]
        assert config.intervals is None
        assert config.ldap is None
        assert config.artifacts_store is not None
        assert config.connections is None
        assert config.operator.enabled is False
        assert config.operator.skip_crd is False

    def test_read_deploy_config_values6(self):
        config = reader.read("tests/fixtures/deployment/values6.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.deployment_chart == "agent"
        assert config.deployment_type == "kubernetes"
        assert config.release_name == "plx"
        assert config.namespace == "polyaxon"
        assert config.limit_resources is False
        assert config.rbac.enabled is True
        assert config.ingress.enabled is False
        assert config.external_services.gateway.host == "foo-bar-ex"
        assert config.external_services.gateway.port == 443
        assert config.external_services.api.host == "foo-bar-ex"
        assert config.external_services.api.port == 443
        assert config.gateway.enabled is None
        assert config.gateway.image == "polyaxon/polyaxon-streams"
        assert config.gateway.concurrency == 4
        assert config.gateway.per_core is False
        assert config.auth.enabled is True
        assert config.auth.external == "test"
        assert config.auth.use_resolver is True
        assert config.operator.enabled is False
        assert config.operator.skip_crd is True
        assert config.proxy.enabled is True
        assert config.proxy.https_proxy == "foo:34/bar"
        assert config.proxy.host == "12.12.12.12"
        assert config.proxy.port == 8080
        assert config.proxy.kind == "transparent"

    def test_read_deploy_config_pgsql_values(self):
        config = reader.read("tests/fixtures/deployment/external_pgsql_values.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress is None
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector is None
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.scheduler is None
        assert config.worker is None
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.email is None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "test"
        assert config.artifacts_store.kind == "host_path"
        assert config.connections is None
        assert config.encryption_secret == "test"
        assert config.agent_secret == "test"
        assert config.platform_secret == "test"
        assert config.ldap is None
        assert config.rabbitmq is None
        assert config.redis is None
        assert config.postgresql.enabled is False
        assert config.external_services.redis is None
        assert config.external_services.rabbitmq is None
        assert config.external_services.postgresql.to_dict() == {
            "user": "polyaxon",
            "password": "polyaxon",
            "database": "postgres",
            "host": "35.226.163.84",
            "port": 1111,
            "pgbouncer": {"foo": "bar", "image": "test"},
            "options": {"sslmode": "require"},
        }

    def test_read_deploy_config_rabbitmq_values(self):
        config = reader.read("tests/fixtures/deployment/external_rabbitmq_values.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress is None
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector is None
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.scheduler is None
        assert config.worker is None
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.email is None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "test"
        assert config.artifacts_store.kind == "host_path"
        assert config.connections is None
        assert config.ldap is None
        assert config.redis is None
        assert config.postgresql is None
        assert config.rabbitmq.enabled is False
        assert config.external_services.redis is None
        assert config.external_services.postgresql is None
        assert config.external_services.rabbitmq.to_dict() == {
            "user": "polyaxon",
            "password": "polyaxon",
            "host": "35.226.163.84",
            "port": 111,
        }

    def test_read_deploy_config_redis_values(self):
        config = reader.read("tests/fixtures/deployment/external_redis_values.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress is None
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector is None
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.scheduler is None
        assert config.worker is None
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.email is None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "test"
        assert config.artifacts_store.kind == "host_path"
        assert config.connections is None
        assert config.ldap is None
        assert config.postgresql is None
        assert config.rabbitmq is None
        assert config.redis.enabled is False
        assert config.external_services.postgresql is None
        assert config.external_services.rabbitmq is None
        assert config.external_services.redis.to_dict() == {
            "usePassword": True,
            "password": "polyaxon",
            "host": "35.226.163.84",
            "port": 111,
        }

    def test_read_deploy_config_redis_rabbitmq_values(self):
        config = reader.read(
            "tests/fixtures/deployment/internal_redis_rabbitmq_values.yml"
        )
        assert isinstance(config, DeploymentConfig)
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress is None
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector is None
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.scheduler is None
        assert config.worker is None
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.email is None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "test"
        assert config.artifacts_store.kind == "host_path"
        assert config.connections is None
        assert config.ldap is None
        assert config.postgresql is None
        assert config.rabbitmq.enabled is True
        assert config.redis.enabled is True
        assert config.external_services is None

    def test_read_deploy_config_monitoring_values(self):
        config = reader.read("tests/fixtures/deployment/external_redis_values.yml")
        assert isinstance(config, DeploymentConfig)
        assert config.namespace is None
        assert config.rbac.enabled is True
        assert config.ui is None
        assert config.timezone is None
        assert config.environment == "staging"
        assert config.ingress is None
        assert config.gateway.service.type == ServiceTypes.CLUSTER_IP
        assert config.user.to_dict() == {"password": "root"}
        assert config.node_selector is None
        assert config.tolerations is None
        assert config.affinity is None
        assert config.limit_resources is None
        assert config.global_replicas is None
        assert config.global_concurrency is None
        assert config.scheduler is None
        assert config.worker is None
        assert config.beat is None
        assert config.api_hooks is None
        assert config.clean_hooks is None
        assert config.email is None
        assert config.host_name is None
        assert config.allowed_hosts is None
        assert config.intervals is None
        assert config.artifacts_store.name == "test"
        assert config.artifacts_store.kind == "host_path"
        assert config.connections is None
        assert config.ldap is None
        assert config.postgresql is None
        assert config.rabbitmq is None
        assert config.redis.enabled is False
        assert config.external_services.postgresql is None
        assert config.external_services.rabbitmq is None
        assert config.external_services.redis.to_dict() == {
            "usePassword": True,
            "password": "polyaxon",
            "host": "35.226.163.84",
            "port": 111,
        }

    def test_read_deploy_config_wrong_values1(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values2.yml")

    def test_read_deploy_config_wrong_values2(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values2.yml")

    def test_read_deploy_config_wrong_values3(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values3.yml")

    def test_read_deploy_config_wrong_values4(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values4.yml")

    def test_read_deploy_config_wrong_values5(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values5.yml")

    def test_read_deploy_config_wrong_values6(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values6.yml")

    def test_read_deploy_config_wrong_values7(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values7.yml")

    def test_read_deploy_config_wrong_values8(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values8.yml")

    def test_read_deploy_config_wrong_values9(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values9.yml")

    def test_read_deploy_config_wrong_values10(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values10.yml")

    def test_read_deploy_config_wrong_values11(self):
        with self.assertRaises(ValidationError):
            reader.read("tests/fixtures/deployment/wrong_values11.yml")

    def test_read_deploy_config_all_platform_values(self):
        config = reader.read("tests/fixtures/deployment/all_platform_values.yml")
        assert isinstance(config, DeploymentConfig)

        config = reader.read(
            "tests/fixtures/deployment/all_external_platform_values.yml"
        )
        assert isinstance(config, DeploymentConfig)

    def test_read_deploy_config_all_agent_values(self):
        config = reader.read("tests/fixtures/deployment/all_agent_values.yml")
        assert isinstance(config, DeploymentConfig)
