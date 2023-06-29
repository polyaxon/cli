import pytest

from polyaxon.auxiliaries import V1PolyaxonInitContainer
from polyaxon.containers.names import INIT_AUTH_CONTAINER
from polyaxon.containers.pull_policy import PullPolicy
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitAuth(BaseConverterTest):
    def test_get_auth_context_init_container(self):
        container = self.converter._get_auth_context_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            run_path=self.converter.run_path,
            env=[],
        )

        assert container.name == INIT_AUTH_CONTAINER
        assert container.image == "foo/foo"
        assert container.command == ["polyaxon", "initializer", "auth"]
        assert container.args is None
        assert container.env == []
        assert container.resources.to_dict() == {"cpus": "1", "memory": "500Mi"}
        assert container.volume_mounts == [
            self.converter._get_auth_context_mount(
                read_only=False, run_path=self.converter.run_path
            ),
        ]
