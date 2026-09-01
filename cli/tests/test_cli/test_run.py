from mock import patch
import os
import pytest

from polyaxon._cli.run import run
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliRun(BaseCommandTestCase):
    @patch("polyaxon._cli.run._run")
    @patch("polyaxon._env_vars.getters.get_project_or_local")
    def test_run_without_cache_option(self, get_project_or_local, run_operation):
        get_project_or_local.return_value = ("owner", None, "project")

        result = self.runner.invoke(
            run,
            [
                "--project=owner/project",
                "--file={}".format(
                    os.path.abspath("tests/fixtures/plain/simple_job.yml")
                ),
            ],
        )

        assert result.exit_code == 0, result.output
        assert run_operation.call_count == 1
