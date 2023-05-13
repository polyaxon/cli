import pytest

from polyaxon.deploy.operators.helm import HelmOperator
from polyaxon.deploy.operators.kubectl import KubectlOperator
from polyaxon.deploy.schemas.deployment import DeploymentConfig, DeploymentTypes
from polyaxon.managers.deploy import DeployConfigManager
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestDeployConfigManager(BaseTestCase):
    def test_default_props(self):
        manager = DeployConfigManager()
        assert manager.deployment_type == DeploymentTypes.KUBERNETES
        assert manager.is_kubernetes is True
        assert isinstance(manager.helm, HelmOperator)
        assert isinstance(manager.kubectl, KubectlOperator)

    def test_deployment_type(self):
        manager = DeployConfigManager(
            config=DeploymentConfig.from_dict(
                {"deploymentType": DeploymentTypes.DOCKER_COMPOSE}
            )
        )
        assert manager.deployment_type == DeploymentTypes.DOCKER_COMPOSE
        assert manager.is_docker_compose is True

        manager = DeployConfigManager(
            config=DeploymentConfig.from_dict(
                {"deploymentType": DeploymentTypes.KUBERNETES}
            )
        )
        assert manager.deployment_type == DeploymentTypes.KUBERNETES
        assert manager.is_kubernetes is True

        manager = DeployConfigManager(
            config=DeploymentConfig.from_dict(
                {"deploymentType": DeploymentTypes.HEROKU}
            )
        )
        assert manager.deployment_type == DeploymentTypes.HEROKU
        assert manager.is_heroku is True

        manager = DeployConfigManager(
            config=DeploymentConfig.from_dict(
                {"deploymentType": DeploymentTypes.DOCKER}
            )
        )
        assert manager.deployment_type == DeploymentTypes.DOCKER
        assert manager.is_docker is True
