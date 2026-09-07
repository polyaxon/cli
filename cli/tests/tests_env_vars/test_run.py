from mock import patch
from pathlib import Path
import tempfile

from polyaxon._env_vars.getters import get_project_run_or_local, get_run_or_local
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


RUN_UUID = "8aac02e3a62a4f0aaa257c59da5eab80"
EXPLICIT_RUN_UUID = "91b413a2607a41b5b6fa98f3c7df7275"


class TestRunEnvVars(BaseTestCase):
    def test_get_run_or_local(self):
        assert get_run_or_local("uuid") == "uuid"


class TestCachedRunEnvVars(BaseTestCase):
    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.local_cache = Path(directory.name) / "local" / ".polyaxon"
        self.global_cache = Path(directory.name) / "global" / ".polyaxon"
        for manager in (ProjectConfigManager, RunConfigManager):
            patcher = patch.multiple(
                manager,
                CONFIG_PATH=None,
                _PROJECT=str(self.local_cache),
                _PROJECT_PATH=str(self.global_cache),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def cache_project(self, owner="owner", project="project-a", visibility="local"):
        ProjectConfigManager.set_config(
            V1Project(owner=owner, name=project), visibility=visibility
        )

    def cache_run(self, owner="owner", project="project-a", visibility="local"):
        RunConfigManager.set_config(
            V1Run(uuid=RUN_UUID, owner=owner, project=project), visibility=visibility
        )

    def test_matching_local_cache(self):
        self.cache_project()
        self.cache_run()

        assert get_project_run_or_local(is_cli=False) == (
            "owner",
            None,
            "project-a",
            RUN_UUID,
        )

    def test_matching_global_cache(self):
        self.cache_project(visibility="global")
        self.cache_run(visibility="global")

        assert get_project_run_or_local(is_cli=False) == (
            "owner",
            None,
            "project-a",
            RUN_UUID,
        )

    def test_local_cache_overrides_global_cache(self):
        self.cache_project(owner="other-owner", visibility="global")
        self.cache_run(owner="other-owner", visibility="global")
        self.cache_project()
        self.cache_run()

        assert get_project_run_or_local(is_cli=False) == (
            "owner",
            None,
            "project-a",
            RUN_UUID,
        )

    def test_explicit_project_overrides_project_cache(self):
        self.cache_project(project="project-b")
        self.cache_run()

        assert get_project_run_or_local("owner/project-a", is_cli=False) == (
            "owner",
            None,
            "project-a",
            RUN_UUID,
        )

    def test_explicit_project_rejects_conflicting_cached_run(self):
        self.cache_project()
        self.cache_run()

        with self.assertRaises(PolyaxonClientException) as error:
            get_project_run_or_local("owner/project-b", is_cli=False)

        message = str(error.exception)
        assert "owner/project-a" in message
        assert "owner/project-b" in message
        assert RUN_UUID in message
        assert str(self.local_cache / ".run") in message

    def test_same_project_slug_with_different_owner_is_rejected(self):
        self.cache_project(owner="other-owner")
        self.cache_run()

        with self.assertRaises(PolyaxonClientException) as error:
            get_project_run_or_local(is_cli=False)

        assert "owner/project-a" in str(error.exception)
        assert "other-owner/project-a" in str(error.exception)

    def test_cached_owner_team_is_normalized(self):
        self.cache_project(owner="owner/team")
        self.cache_run(owner="owner/team")

        assert get_project_run_or_local(is_cli=False) == (
            "owner",
            "team",
            "project-a",
            RUN_UUID,
        )

    def test_local_project_with_conflicting_global_run_is_rejected(self):
        self.cache_project(project="project-b")
        self.cache_project(visibility="global")
        self.cache_run(visibility="global")

        with self.assertRaises(PolyaxonClientException) as error:
            get_project_run_or_local(is_cli=False)

        message = str(error.exception)
        assert "owner/project-a" in message
        assert "owner/project-b" in message
        assert str(self.global_cache / ".run") in message

    def test_explicit_uuid_ignores_conflicting_cached_run(self):
        self.cache_project()
        self.cache_run()

        assert get_project_run_or_local(
            "other-owner/project-b", EXPLICIT_RUN_UUID, is_cli=False
        ) == ("other-owner", None, "project-b", EXPLICIT_RUN_UUID)

    def test_explicit_uuid_with_cached_project_ignores_cached_run(self):
        self.cache_project(project="project-b")
        self.cache_run()

        assert get_project_run_or_local(run_uuid=EXPLICIT_RUN_UUID, is_cli=False) == (
            "owner",
            None,
            "project-b",
            EXPLICIT_RUN_UUID,
        )

    def test_incomplete_cached_ownership_is_allowed(self):
        self.cache_project()
        for owner, project in ((None, None), ("owner", None), (None, "project-a")):
            with self.subTest(owner=owner, project=project):
                self.cache_run(owner=owner, project=project)

                assert get_project_run_or_local(is_cli=False) == (
                    "owner",
                    None,
                    "project-a",
                    RUN_UUID,
                )

    def test_incomplete_cache_still_rejects_known_conflict(self):
        self.cache_project()
        for owner, project in (("other-owner", None), (None, "project-b")):
            with self.subTest(owner=owner, project=project):
                self.cache_run(owner=owner, project=project)

                with self.assertRaises(PolyaxonClientException):
                    get_project_run_or_local(is_cli=False)
