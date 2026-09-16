import io
import os
import pytest
from unittest.mock import mock_open, patch

from polyaxon._managers.ignore import IgnoreConfigManager
from polyaxon._utils import cli_constants
from polyaxon._utils.cli_constants import SYMLINK_MODES
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


@pytest.mark.managers_mark
class TestIgnoreConfigManagerUploads:
    @pytest.fixture
    def upload_root(self, tmp_path, monkeypatch):
        root = tmp_path / "upload"
        root.mkdir()
        monkeypatch.chdir(root)
        return root

    @pytest.mark.parametrize(
        "relative,expected",
        [
            (".", True),
            ("child/file.txt", True),
            ("..", False),
            ("../upload-other", False),
        ],
    )
    def test_is_inside_root(self, upload_root, relative, expected):
        target = os.path.abspath(upload_root / relative)
        assert IgnoreConfigManager._is_inside_root(target, str(upload_root)) is expected

    def test_is_inside_root_rejects_incompatible_paths(self, upload_root):
        assert (
            IgnoreConfigManager._is_inside_root("relative/path", str(upload_root))
            is False
        )

    @pytest.mark.parametrize(
        "relative,is_dir,patterns,expected",
        [
            ("private/nested/file.txt", False, ["private/"], True),
            ("private", True, ["private/"], True),
            ("private", False, ["private/"], False),
            ("private/file.txt", False, ["private/", "!private/"], False),
            (".polyaxon/file.txt", False, ["./.polyaxon"], True),
            ("public/file.txt", False, ["private/"], False),
        ],
    )
    def test_is_ignored_target_checks_target_and_ancestors(
        self, upload_root, relative, is_dir, patterns, expected
    ):
        root = os.path.realpath(upload_root)
        assert (
            IgnoreConfigManager._is_ignored_target(
                target=os.path.join(root, relative),
                is_dir=is_dir,
                path=".",
                upload_root=root,
                config=IgnoreConfigManager.get_patterns(patterns),
            )
            is expected
        )

    @pytest.mark.parametrize(
        "mode,expected",
        [
            ("skip", (False, "skipped")),
            ("error", (False, "symlinks are forbidden")),
            ("resolve-safe", (True, None)),
            ("resolve-all", (True, None)),
        ],
    )
    @pytest.mark.parametrize("ignored", [False, True])
    def test_check_path_distinguishes_ignored_and_reported_links(
        self, upload_root, mode, expected, ignored
    ):
        (upload_root / "content.txt").write_text("content")
        link = upload_root / "link"
        link.symlink_to("content.txt")
        config = IgnoreConfigManager.get_patterns(["link"] if ignored else [])

        assert IgnoreConfigManager._check_path(
            str(link),
            path=str(upload_root),
            upload_root=os.path.realpath(upload_root),
            config=config,
            symlink_mode=mode,
        ) == ((False, None) if ignored else expected)

    @pytest.mark.parametrize("relative", ["alias", "alias/content.txt"])
    def test_check_path_ignores_targets_beneath_directory_links(
        self, upload_root, relative
    ):
        (upload_root / ".venv").mkdir()
        (upload_root / ".venv" / "content.txt").write_text("content")
        (upload_root / "alias").symlink_to(".venv", target_is_directory=True)

        assert IgnoreConfigManager._check_path(
            str(upload_root / relative),
            path=str(upload_root),
            upload_root=os.path.realpath(upload_root),
            config=IgnoreConfigManager.get_patterns([".venv/"]),
            symlink_mode="resolve-safe",
            is_dir=relative == "alias",
            through_link=relative != "alias",
        ) == (False, None)

    @pytest.mark.parametrize(
        "target,mode,expected",
        [
            (
                "external",
                "resolve-safe",
                (False, "link target is outside the upload root"),
            ),
            ("external", "resolve-all", (True, None)),
            ("missing", "resolve-safe", (False, "broken link or symlink cycle")),
            (".", "resolve-safe", (False, "directory symlink cycle")),
        ],
    )
    def test_check_path_validates_resolved_links(
        self, upload_root, target, mode, expected
    ):
        if target == "external":
            target = upload_root.parent / "outside.txt"
            target.write_text("external")
        link = upload_root / "link"
        link.symlink_to(target)

        assert (
            IgnoreConfigManager._check_path(
                str(link),
                path=str(upload_root),
                upload_root=os.path.realpath(upload_root),
                config=[],
                symlink_mode=mode,
                is_dir=link.is_dir(),
            )
            == expected
        )

    @pytest.mark.parametrize("mode", ["resolve-safe", "resolve-all"])
    def test_upload_symlink_internal_targets_and_aliases(self, upload_root, mode):
        source = upload_root / "source"
        source.mkdir()
        (source / "content.txt").write_text("content")
        (upload_root / "file-link").symlink_to("source/content.txt")
        (upload_root / "first").symlink_to("source", target_is_directory=True)
        (upload_root / "second").symlink_to("source", target_is_directory=True)
        (upload_root / "empty").mkdir()
        (upload_root / "empty-link").symlink_to("empty", target_is_directory=True)

        files = IgnoreConfigManager.get_unignored_filepaths(
            str(upload_root), symlink_mode=mode
        )

        assert {os.path.relpath(f, upload_root) for f in files} == {
            "source/content.txt",
            "file-link",
            "first",
            "first/content.txt",
            "second",
            "second/content.txt",
            "empty-link",
        }

    @pytest.mark.parametrize("is_dir", [False, True])
    def test_upload_symlink_external_targets_require_opt_in(self, upload_root, is_dir):
        target = upload_root.parent / "upload-other"
        if is_dir:
            target.mkdir()
            (target / "content.txt").write_text("external")
        else:
            target.write_text("external")
        link = upload_root / "link"
        link.symlink_to(target, target_is_directory=is_dir)

        with pytest.raises(PolyaxonClientException, match="outside the upload root"):
            IgnoreConfigManager.get_unignored_filepaths(
                str(upload_root), symlink_mode="resolve-safe"
            )

        files = IgnoreConfigManager.get_unignored_filepaths(
            str(upload_root), symlink_mode="resolve-all"
        )
        expected = {str(link), str(link / "content.txt")} if is_dir else {str(link)}
        assert set(files) == expected

    @pytest.mark.parametrize("mode", ["resolve-safe", "resolve-all"])
    @pytest.mark.parametrize("target", ["missing", "link", "."])
    def test_upload_symlink_broken_targets_and_cycles(self, upload_root, mode, target):
        (upload_root / "link").symlink_to(target)
        with pytest.raises(PolyaxonClientException, match="broken|cycle"):
            IgnoreConfigManager.get_unignored_filepaths(
                str(upload_root), symlink_mode=mode
            )

    @pytest.mark.parametrize("mode", ["skip", "error"])
    def test_upload_symlink_file_directory_and_broken_links(self, upload_root, mode):
        source = upload_root / "source"
        source.mkdir()
        (source / "content.txt").write_text("content")
        (upload_root / "file-link").symlink_to("source/content.txt")
        (upload_root / "directory-link").symlink_to("source", target_is_directory=True)
        (upload_root / "broken-link").symlink_to("missing")

        if mode == "error":
            with pytest.raises(
                PolyaxonClientException, match=r"Rejected 3 symlink\(s\)"
            ):
                IgnoreConfigManager.get_unignored_filepaths(
                    str(upload_root), symlink_mode=mode
                )
        else:
            with patch("polyaxon._managers.ignore.logger.warning") as warning:
                files = IgnoreConfigManager.get_unignored_filepaths(
                    str(upload_root), symlink_mode=mode
                )
            assert files == [str(source / "content.txt")]
            assert "Skipped 3 symlink(s)" in warning.call_args.args[0]

    @pytest.mark.parametrize("mode", ["skip", "error"])
    @pytest.mark.parametrize("limit", [0, 2, 20, 25])
    def test_upload_symlink_report_limit(self, upload_root, mode, limit):
        for index in range(25):
            (upload_root / "link-{:02d}".format(index)).symlink_to("missing")
        with patch("polyaxon._managers.ignore.logger.warning") as warning:
            if mode != "skip":
                with pytest.raises(PolyaxonClientException) as error:
                    IgnoreConfigManager.get_unignored_filepaths(
                        str(upload_root), symlink_mode=mode, symlink_report_limit=limit
                    )
                message = str(error.value)
            else:
                assert (
                    IgnoreConfigManager.get_unignored_filepaths(
                        str(upload_root), symlink_mode=mode, symlink_report_limit=limit
                    )
                    == []
                )
                message = warning.call_args.args[0]
        assert "25 symlink(s)" in message
        assert message.count(" -> ") == limit
        if limit < 25:
            assert "{} more symlink(s) not shown".format(25 - limit) in message
        else:
            reported = [
                line.split(" -> ", 1)[0]
                for line in message.splitlines()
                if " -> " in line
            ]
            expected = [str(upload_root / "link-{:02d}".format(i)) for i in range(25)]
            assert sorted(reported) == sorted(expected)

    def test_upload_symlink_defaults_to_skip_with_bounded_warning(self, upload_root):
        (upload_root / "source").mkdir()
        (upload_root / "source" / "content.txt").write_text("content")
        (upload_root / "file-link").symlink_to("source/content.txt")
        (upload_root / "directory-link").symlink_to("source", target_is_directory=True)
        (upload_root / "broken-link").symlink_to("missing")
        (upload_root / "cycle-link").symlink_to(".", target_is_directory=True)
        with patch("polyaxon._managers.ignore.logger.warning") as warning:
            files = IgnoreConfigManager.get_unignored_filepaths(
                str(upload_root), symlink_report_limit=2
            )
        assert files == [str(upload_root / "source" / "content.txt")]
        warning.assert_called_once()
        message = warning.call_args.args[0]
        assert "Skipped 4 symlink(s)" in message
        assert message.count(" -> ") == 2
        assert "2 more symlink(s) not shown" in message

    @pytest.mark.parametrize("mode", SYMLINK_MODES)
    def test_upload_symlink_ignored_links_do_not_fail(self, upload_root, mode):
        (upload_root / ".polyaxonignore").write_text("link\n")
        (upload_root / "link").symlink_to("../missing")
        with patch("polyaxon._managers.ignore.logger.warning") as warning:
            files = IgnoreConfigManager.get_unignored_filepaths(
                str(upload_root), symlink_mode=mode
            )
        assert files == [str(upload_root / ".polyaxonignore")]
        warning.assert_not_called()

    @pytest.mark.parametrize("mode", ["resolve-safe", "resolve-all"])
    def test_upload_symlink_targets_cannot_bypass_default_ignores(
        self, upload_root, mode
    ):
        (upload_root / ".venv").mkdir()
        (upload_root / ".venv" / "secret.txt").write_text("secret")
        (upload_root / ".venv" / "broken").symlink_to("missing")
        (upload_root / ".polyaxon").mkdir()
        (upload_root / ".polyaxon" / "broken").symlink_to("missing")
        (upload_root / "directory-alias").symlink_to(".venv", target_is_directory=True)
        (upload_root / "file-alias").symlink_to(".venv/secret.txt")
        (upload_root / "broken-alias").symlink_to(".venv/missing")

        assert IgnoreConfigManager.get_unignored_filepaths(symlink_mode=mode) == []

    def test_upload_symlink_custom_ignores_apply_to_alias_children(self, upload_root):
        (upload_root / ".polyaxonignore").write_text("alias/private.txt\n*.skip\n")
        source = upload_root / ".venv"
        source.mkdir()
        (source / "private.txt").write_text("content")
        (source / "ignored.skip").write_text("excluded")
        (upload_root / "alias").symlink_to(".venv", target_is_directory=True)

        files = IgnoreConfigManager.get_unignored_filepaths(
            str(upload_root), symlink_mode="resolve-safe"
        )
        names = {os.path.relpath(f, upload_root) for f in files}
        assert ".venv/private.txt" in names
        assert "alias/private.txt" not in names
        assert not any(name.endswith(".skip") for name in names)

    @pytest.mark.parametrize("mode", SYMLINK_MODES)
    def test_upload_regular_files_do_not_resolve_each_target(self, upload_root, mode):
        source = upload_root / "source"
        source.mkdir()
        content = source / "content.txt"
        content.write_text("content")
        with patch(
            "polyaxon._managers.ignore.os.path.realpath", wraps=os.path.realpath
        ) as realpath:
            assert IgnoreConfigManager.get_unignored_filepaths(
                str(upload_root), symlink_mode=mode
            ) == [str(content)]
        assert str(content) not in [call.args[0] for call in realpath.call_args_list]

    @pytest.mark.parametrize(
        "options",
        [
            {"symlink_mode": "unknown"},
            {"symlink_mode": "preserve"},
            {"symlink_report_limit": -1},
        ],
    )
    def test_upload_symlink_invalid_options(self, upload_root, options):
        with pytest.raises(PolyaxonClientException):
            IgnoreConfigManager.get_unignored_filepaths(str(upload_root), **options)


@pytest.mark.managers_mark
class TestIgnoreConfigManager(BaseTestCase):
    """Mock the config ignore file."""

    def test_default_props(self):
        assert IgnoreConfigManager.is_global() is False
        assert IgnoreConfigManager.is_local() is True
        assert IgnoreConfigManager.IN_PROJECT_DIR is False
        assert IgnoreConfigManager.CONFIG_FILE_NAME == ".polyaxonignore"
        assert IgnoreConfigManager.CONFIG is None

    @staticmethod
    def get_ignored(patterns):
        return [r.pattern for r in patterns if r.is_exclude]

    @staticmethod
    def get_allowed(patterns):
        return [r.pattern for r in patterns if not r.is_exclude]

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_ignored_lines(self, mock_file, _):
        configs = [
            ("foo.c", "foo.[dh]"),
            ("foo/foo.c", "/foo.c"),
            ("foo/foo.c", "/*.c"),
            ("foo/bar/", "/bar/"),
            ("foo/bar/", "foo/bar/*"),
            ("foo/bar", "foo?bar"),
        ]
        for path, pattern in configs:
            mock_file.return_value.__enter__.return_value = [pattern]
            patterns = IgnoreConfigManager.get_config()
            self.assertEqual(
                (self.get_ignored(patterns), self.get_allowed(patterns)),
                ([pattern], []),
            )
            assert list(IgnoreConfigManager.find_matching(path, patterns)) == []

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_allowed_list_lines(self, mock_file, _):
        configs = [
            ("foo.c", "*.c"),
            (".c", "*.c"),
            ("foo/foo.c", "*.c"),
            ("foo/foo.c", "foo.c"),
            ("foo.c", "/*.c"),
            ("foo.c", "/foo.c"),
            ("foo.c", "foo.c"),
            ("foo.c", "foo.[ch]"),
            ("foo/bar/bla.c", "foo/**"),
            ("foo/bar/bla/blie.c", "foo/**/blie.c"),
            ("foo/bar/bla.c", "**/bla.c"),
            ("bla.c", "**/bla.c"),
            ("foo/bar", "foo/**/bar"),
            ("foo/bla/bar", "foo/**/bar"),
            ("foo/bar/", "bar/"),
            ("foo/bar/", "bar"),
            ("foo/bar/something", "foo/bar/*"),
        ]
        for path, pattern in configs:
            mock_file.return_value.__enter__.return_value = [pattern]
            patterns = IgnoreConfigManager.get_config()
            self.assertEqual(
                (self.get_ignored(patterns), self.get_allowed(patterns)),
                ([pattern], []),
            )
            assert len(list(IgnoreConfigManager.find_matching(path, patterns))) == 1

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_ignores_commented_lines(self, mock_file, _):
        file_data = ["", "# comment", "", "*.py"]
        mock_file.return_value.__enter__.return_value = file_data

        patterns = IgnoreConfigManager.get_config()
        self.assertEqual(
            (self.get_ignored(patterns), self.get_allowed(patterns)), (["*.py"], [])
        )

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_trims_slash_prefix_from_abs_paths(self, mock_file, _):
        file_data = ["/test", "!/ignore"]
        mock_file.return_value.__enter__.return_value = file_data

        patterns = IgnoreConfigManager.get_config()
        self.assertEqual(
            (self.get_ignored(patterns), self.get_allowed(patterns)),
            (["/test"], ["/ignore"]),
        )

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_properly_interprets_allowed_list_globs(self, mock_file, _):
        file_data = ["", "# comment", "*.py", "!file1.py"]
        mock_file.return_value.__enter__.return_value = file_data

        patterns = IgnoreConfigManager.get_config()
        self.assertEqual(
            (self.get_ignored(patterns), self.get_allowed(patterns)),
            (["*.py"], ["file1.py"]),
        )

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=False)
    def test_returns_two_empty_lists_if_file_is_not_present(self, _):
        patterns = IgnoreConfigManager.get_config()
        self.assertEqual(
            patterns,
            IgnoreConfigManager.get_patterns(
                io.StringIO(cli_constants.DEFAULT_IGNORE_LIST)
            ),
        )

    @patch("polyaxon._managers.ignore.os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_escaping_of_globs_that_start_with_reserved_chars(self, mock_file, _):
        file_data = ["", r"# comment", r"\#file1", r"\!file2"]  # noqa
        mock_file.return_value.__enter__.return_value = file_data

        patterns = IgnoreConfigManager.get_config()
        self.assertEqual(
            (self.get_ignored(patterns), self.get_allowed(patterns)),
            (["#file1", "!file2"], []),
        )
