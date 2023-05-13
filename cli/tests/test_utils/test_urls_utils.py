import pytest

from unittest import TestCase
from unittest.mock import MagicMock

from polyaxon.utils.urls_utils import (
    get_fqn_run_url,
    get_owner_project_url,
    get_owner_url,
    get_project_url,
    get_run_health_url,
    get_run_url,
)


@pytest.mark.utils_mark
class TestUrlsUtils(TestCase):
    def setUp(self):
        super().setUp()
        self.user = MagicMock(username="foo")
        unique_name = f"{self.user.username}.project-test"
        self.project = MagicMock(
            id=1, name="project-test", user=self.user, unique_name=unique_name
        )
        unique_name = f"{unique_name}.uuid"
        self.run = MagicMock(
            uuid="uuid", id=2, project=self.project, unique_name=unique_name
        )

    def test_get_owner_url(self):
        self.assertEqual(get_owner_url("foo"), "/foo")

    def test_get_project_url(self):
        unique_name = self.project.unique_name
        self.assertEqual(
            get_project_url(unique_name=unique_name),
            "/{}".format(unique_name.replace(".", "/")),
        )

    def test_get_owner_project_url(self):
        self.assertEqual(
            get_owner_project_url(owner="foo", project_name="bar"), "/foo/bar"
        )

    def test_get_run_url(self):
        self.assertEqual(
            get_run_url(
                owner="foo", project_name="project-test", run_uuid=self.run.uuid
            ),
            "/foo/project-test/runs/uuid",
        )

    def test_get_fqn_run_url(self):
        unique_name = self.run.unique_name
        self.assertEqual(
            get_fqn_run_url(unique_name=unique_name), "/foo/project-test/runs/uuid"
        )

    def test_get_run_health_url(self):
        self.assertEqual(
            get_run_health_url(unique_name=self.run.unique_name),
            "{}/_heartbeat".format(get_fqn_run_url(self.run.unique_name)),
        )
