from polyaxon._env_vars.getters import get_project_error_message, get_project_or_local
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


class TestProjectEnvVars(BaseTestCase):
    def test_get_project_error_message(self):
        assert get_project_error_message("", "") is not None
        assert get_project_error_message("test", "") is not None
        assert get_project_error_message("", "test") is not None
        assert get_project_error_message("test", "test") is None

    def test_get_project_or_local(self):
        with self.assertRaises(PolyaxonClientException):
            get_project_or_local(None)

        assert get_project_or_local("owner.project") == ("owner", None, "project")
        assert get_project_or_local("owner.team.project") == (
            "owner",
            "team",
            "project",
        )
