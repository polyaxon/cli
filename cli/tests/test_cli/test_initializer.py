from mock import patch
import pytest

from polyaxon._cli.services.initializer import initializer
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliInitializerGit(BaseCommandTestCase):
    def setUp(self):
        super().setUp()
        for name in ("get_client_or_raise", "set_remote"):
            patcher = patch("polyaxon._init.git.{}".format(name), return_value=None)
            patcher.start()
            self.addCleanup(patcher.stop)
        clone_patcher = patch("polyaxon._init.git.clone_and_checkout_git_repo")
        self.clone = clone_patcher.start()
        self.addCleanup(clone_patcher.stop)
        fetch_patcher = patch("polyaxon._init.git.fetch_git_repo")
        self.fetch = fetch_patcher.start()
        self.addCleanup(fetch_patcher.stop)

    def invoke(self, flags):
        result = self.runner.invoke(
            initializer,
            [
                "git",
                "--url=https://github.com/octocat/Hello-World.git",
                "--repo-path=/tmp/plx/repo",
                "--flags={}".format(flags),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_json_one_flag(self):
        self.invoke('["--depth=1"]')
        assert self.clone.call_args.kwargs["flags"] == ["--depth=1"]
        assert self.fetch.call_count == 0

    def test_json_several_flags(self):
        self.invoke('["--depth=1","--recurse-submodules","-c http.extraHeader=a,b"]')
        assert self.clone.call_args.kwargs["flags"] == [
            "--depth=1",
            "--recurse-submodules",
            "-c http.extraHeader=a,b",
        ]
        assert self.fetch.call_count == 0

    def test_json_experimental_fetch(self):
        self.invoke('["--experimental-fetch","--depth=1"]')
        assert self.fetch.call_args.kwargs["flags"] == ["--depth=1"]
        assert self.clone.call_count == 0

    def test_comma_flags(self):
        self.invoke("--depth=1,--recurse-submodules")
        assert self.clone.call_args.kwargs["flags"] == [
            "--depth=1",
            "--recurse-submodules",
        ]
        assert self.fetch.call_count == 0
