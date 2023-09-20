from mock import patch

from polyaxon._env_vars.getters import get_project_run_or_local, get_run_or_local
from polyaxon._utils.test_utils import BaseTestCase


class TestRunEnvVars(BaseTestCase):
    def test_get_run_or_local(self):
        assert get_run_or_local("uuid") == "uuid"

    @patch("polyaxon._env_vars.getters.run.get_project_or_local")
    @patch("polyaxon._env_vars.getters.run.get_run_or_local")
    def test_get_project_run_or_local(
        self, get_run_or_local_mock, get_project_or_local_mock
    ):
        get_project_or_local_mock.return_value = ("owner", "project")
        get_run_or_local_mock.return_value = "uuid"

        assert get_project_run_or_local() == ("owner", "project", "uuid")
