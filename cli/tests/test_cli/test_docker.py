import pytest

from mock import patch

from polyaxon._cli.services.docker import docker
from polyaxon._schemas.types.dockerfile import V1DockerfileType
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliDocker(BaseCommandTestCase):
    @patch("polyaxon._docker.builder.generator.DockerFileGenerator.create")
    def test_docker_build_context(self, generate_create):
        build_context = V1DockerfileType(image="foo")
        self.runner.invoke(
            docker,
            ["generate", "--build-context={}".format(build_context.to_json())],
        )
        assert generate_create.call_count == 1
