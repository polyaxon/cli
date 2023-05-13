import pytest

from mock import patch

from polyaxon.cli.projects import project
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliProject(BaseCommandTestCase):
    @patch("polyaxon.client.ProjectClient.create")
    def test_create_project(self, create_project):
        self.runner.invoke(project, ["create"])
        assert create_project.call_count == 0
        self.runner.invoke(project, ["create", "--name=owner/foo"])
        assert create_project.call_count == 1

    @patch("polyaxon.client.ProjectClient.list")
    def test_list_projects(self, list_projects):
        self.runner.invoke(project, ["ls", "--owner=owner"])
        assert list_projects.call_count == 1

    @patch("polyaxon.client.ProjectClient.refresh_data")
    def test_get_project(self, get_project):
        self.runner.invoke(project, ["-p", "admin/foo", "get"])
        assert get_project.call_count == 1

    @patch("polyaxon.client.ProjectClient.update")
    def test_update_project(self, update_project):
        self.runner.invoke(project, ["update"])
        assert update_project.call_count == 0

        self.runner.invoke(project, ["-p", "admin/foo", "update", "--description=foo"])
        assert update_project.call_count == 1
