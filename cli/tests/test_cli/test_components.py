import pytest

from mock import patch

from polyaxon.cli.components import components
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliComponent(BaseCommandTestCase):
    @patch("polyaxon.sdk.api.ProjectsV1Api.create_version")
    @patch("polyaxon.sdk.api.ProjectsV1Api.get_version")
    def test_create_component(self, get_version, create_component):
        self.runner.invoke(components, ["push"])
        assert create_component.call_count == 0
        assert get_version.call_count == 0
        self.runner.invoke(components, ["push", "--name=owner/foo"])
        assert get_version.call_count == 0
        assert create_component.call_count == 0

    @patch("polyaxon.sdk.api.ProjectsV1Api.list_versions")
    def test_list_components(self, list_components):
        self.runner.invoke(components, ["ls", "--project=owner/foo"])
        assert list_components.call_count == 1

    @patch("polyaxon.sdk.api.ProjectsV1Api.get_version")
    def test_get_components(self, get_components):
        self.runner.invoke(components, ["get", "-p", "admin/foo"])
        assert get_components.call_count == 1

    @patch("polyaxon.sdk.api.ProjectsV1Api.patch_version")
    def test_update_components(self, update_components):
        self.runner.invoke(
            components, ["update", "-p", "admin/foo", "--description=foo"]
        )
        assert update_components.call_count == 1

    @patch("polyaxon.sdk.api.ProjectsV1Api.create_version_stage")
    def test_update_artifact_stage(self, stage_component):
        self.runner.invoke(
            components,
            ["stage", "-p", "admin/foo", "-to", "production", "--reason=foo"],
        )
        assert stage_component.call_count == 1
