import mock
import pytest

from urllib3.exceptions import ReadTimeoutError

from polyaxon._docker.builder import DockerBuilder, DockerPusher, build, build_and_push
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonBuildException


@pytest.mark.docker_mark
class TestDockerBuilder(BaseTestCase):
    @staticmethod
    def touch(path):
        with open(path, "w") as f:
            f.write("test")

    @mock.patch("docker.APIClient.images")
    def test_check_image(self, check_image):
        builder = DockerBuilder(context=".", destination="image:tag")
        builder.check_image()
        assert check_image.call_count == 1
        assert check_image.call_args[0] == ("image:tag",)

    def test_validate_registries(self):
        with self.assertRaises(PolyaxonBuildException):
            DockerBuilder(context=".", destination="image:tag", registries=["foo"])

        with self.assertRaises(PolyaxonBuildException):
            DockerBuilder(
                context=".",
                destination="image:tag",
                registries=["https://user@pwd:host"],
            )

        builder = DockerBuilder(
            context=".",
            destination="image:tag",
            registries=["https://user:pwd@host.ca"],
        )

        assert builder.registries is not None

    @mock.patch("docker.APIClient.login")
    def test_login_registries(self, login_mock):
        builder = DockerBuilder(
            context=".",
            destination="image:tag",
            registries=[
                "https://user:pass@siteweb.ca",
                "https://user@pwd:8000",
            ],
        )
        builder.login_private_registries()
        assert login_mock.call_count == 2

    @mock.patch("docker.APIClient.build")
    def test_build(self, build_mock):
        builder = DockerBuilder(context=".", destination="image:tag")
        builder.build()
        assert build_mock.call_count == 1

    @mock.patch("docker.APIClient.push")
    def test_push(self, push_mock):
        builder = DockerPusher(destination="image:tag")
        builder.push()
        assert push_mock.call_count == 1


@pytest.mark.docker_mark
class TestBuilder(BaseTestCase):
    @mock.patch("docker.APIClient.build")
    @mock.patch("docker.APIClient.login")
    @mock.patch("docker.APIClient.images")
    def test_build_no_login(self, images_mock, login_mock, build_mock):
        build(
            context=".",
            destination="image_name:image_tag",
            nocache=True,
            registries=None,
        )
        assert images_mock.call_count == 1
        assert login_mock.call_count == 0
        assert build_mock.call_count == 1

    @mock.patch("docker.APIClient.build")
    @mock.patch("docker.APIClient.login")
    @mock.patch("docker.APIClient.images")
    def test_build_login(self, images_mock, login_mock, build_mock):
        build(
            context=".",
            destination="image_name:image_tag",
            nocache=True,
            registries=[
                "https://user:pass@siteweb.ca",
                "https://user:pass@siteweb.ca",
            ],
        )
        assert images_mock.call_count == 1
        assert login_mock.call_count == 2
        assert build_mock.call_count == 1

    @mock.patch("docker.APIClient.push")
    @mock.patch("docker.APIClient.build")
    @mock.patch("docker.APIClient.login")
    @mock.patch("docker.APIClient.images")
    def test_build_and_push(self, images_mock, login_mock, build_mock, push_mock):
        build_and_push(
            context=".",
            destination="image_name:image_tag",
            nocache=True,
            registries=[
                "https://user:pass@siteweb.ca",
                "https://user:pass@siteweb.ca",
            ],
        )
        assert images_mock.call_count == 1
        assert login_mock.call_count == 2
        assert build_mock.call_count == 1
        assert push_mock.call_count == 1

    @mock.patch("docker.APIClient.build")
    @mock.patch("docker.APIClient.images")
    def test_build_raise_timeout(self, images_mock, build_mock):
        build_mock.side_effect = ReadTimeoutError(None, "foo", "error")
        with self.assertRaises(PolyaxonBuildException):
            build(
                context=".",
                destination="image_name:image_tag",
                nocache=True,
                max_retries=1,
                sleep_interval=0,
            )
        assert images_mock.call_count == 1

    @mock.patch("docker.APIClient.push")
    @mock.patch("docker.APIClient.build")
    @mock.patch("docker.APIClient.images")
    def test_push_raise_timeout(self, images_mock, build_mock, push_mock):
        push_mock.side_effect = ReadTimeoutError(None, "foo", "error")
        with self.assertRaises(PolyaxonBuildException):
            build_and_push(
                context=".",
                destination="image_name:image_tag",
                nocache=True,
                max_retries=1,
                sleep_interval=0,
            )
        assert images_mock.call_count == 1
        assert build_mock.call_count == 1
        assert push_mock.call_count == 1
