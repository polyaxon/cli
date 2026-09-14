from polyaxon._env_vars.getters import get_project_error_message
from polyaxon._env_vars.getters.project import _get_project_context
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


class TestProjectEnvVars(BaseTestCase):
    def test_get_project_error_message(self):
        assert get_project_error_message("", "") is not None
        assert get_project_error_message("test", "") is not None
        assert get_project_error_message("", "test") is not None
        assert get_project_error_message("test", "test") is None

    def test_get_project_context(self):
        with self.assertRaises(PolyaxonClientException):
            _get_project_context(None)

        context = _get_project_context("owner.project")
        assert (context.owner, context.team, context.project) == (
            "owner",
            None,
            "project",
        )

        context = _get_project_context("owner.team.project")
        assert (context.owner, context.team, context.project) == (
            "owner",
            "team",
            "project",
        )
