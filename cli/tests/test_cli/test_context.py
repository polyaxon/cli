import logging
import pytest
import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import click
from rich.console import Console
from rich.theme import Theme

from clipped.formatting import Printer
from polyaxon._cli.context import _print_context, report_client_context
from polyaxon._env_vars.getters._context import _ContextSource
from polyaxon._env_vars.getters.project import _ProjectContext


pytestmark = pytest.mark.cli_mark


@pytest.fixture
def make_console(monkeypatch):
    theme = Theme(
        {name: Printer.stderr_console.get_style(name) for name in ("header", "warning")}
    )

    def make(width=160, color=False):
        monkeypatch.setattr(
            Printer,
            "stderr_console",
            Console(
                stderr=True,
                width=width,
                force_terminal=color,
                color_system="standard" if color else None,
                no_color=not color,
                theme=theme,
            ),
        )

    return make


def test_context_keeps_sources_on_their_rows(make_console, capsys):
    make_console()
    _print_context(
        [
            (
                "Owner",
                "acme",
                _ContextSource("global cache", "/home/user/.polyaxon/.user"),
            ),
            ("Project", "quick-start", _ContextSource()),
        ]
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines()[0] == "Context:"
    assert [
        line.rstrip().split(None, 2)
        for line in captured.err.splitlines()[1:]
        if line.strip()
    ] == [
        ["Owner", "acme", "global cache · /home/user/.polyaxon/.user"],
        ["Project", "quick-start", "explicit"],
    ]
    assert "\x1b[" not in captured.err


def test_project_team_is_consistent_in_cli_and_python_reporting(
    make_console, capsys, caplog
):
    make_console()
    caplog.set_level(logging.INFO, logger="polyaxon.cli")
    source = _ContextSource("local cache", "/work/.polyaxon/.project")
    context = _ProjectContext("acme", "team", "quick-start", source, source)

    context.report()
    _print_context(context.fields())

    assert "Using cached project `acme/team/quick-start`" in caplog.text
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Owner acme/team" in " ".join(captured.err.split())
    assert "Project quick-start" in " ".join(captured.err.split())


def test_context_uses_cli_heading_and_neutral_value_styles(make_console, capsys):
    make_console(color=True)
    _print_context(
        [("Project", "project-a", _ContextSource("local cache", "/work/.project"))]
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "\x1b[33mContext:\x1b[0m" in captured.err
    assert "\x1b[1mproject-a" in captured.err
    assert "\x1b[2mlocal cache · /work/.project" in captured.err


@pytest.mark.parametrize("width", [60, 80, 160])
def test_context_wraps_without_losing_literal_values(make_console, capsys, width):
    make_console(width=width)
    run_uuid = "11111111111111111111111111111111"
    path = "/work/a directory[red]/:rocket:/another-long-directory/.polyaxon/.run"
    _print_context(
        [
            ("Owner", "owner", _ContextSource()),
            ("Project", "[bold]project", _ContextSource()),
            ("Run", run_uuid, _ContextSource("local cache", path)),
        ]
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    compact = "".join(captured.err.split())
    assert run_uuid in compact
    assert "[bold]project" in compact
    assert "".join(path.split()) in compact
    assert all(len(line) <= width for line in captured.err.splitlines())


def test_context_keeps_incomplete_ownership_warning_separate(make_console, capsys):
    make_console(color=True)
    _print_context(
        [("Run", "run-uuid", _ContextSource("local cache", "/work/.run"))],
        incomplete_run=True,
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("Context:") == 1
    assert "\x1b[33mContext:" in captured.err
    assert "\x1b[35m" in captured.err
    plain = re.sub(r"\x1b\[[0-9;]*m", "", captured.err)
    assert "Cached owner/project metadata is incomplete;" in plain


@pytest.mark.parametrize("show_context", [False, True])
@pytest.mark.parametrize("no_op", [False, True])
def test_client_reporting_uses_context_adapter(
    show_context, no_op, make_console, capsys, monkeypatch
):
    make_console()
    source = _ContextSource("local cache", "/work/.polyaxon/.run")
    context = None if no_op else ([("Run", "run-uuid", source)], True)
    get_context = MagicMock(return_value=context)
    monkeypatch.setattr("polyaxon._cli.context._get_client_context", get_context)
    client = SimpleNamespace()

    report_client_context(client, include_run=True, show_context=show_context)

    captured = capsys.readouterr()
    assert captured.out == ""
    if show_context:
        get_context.assert_called_once_with(client, include_run=True)
    else:
        get_context.assert_not_called()

    if show_context and not no_op:
        assert captured.err.count("Context:") == 1
        assert source.path in captured.err
        assert "Cached owner/project metadata is incomplete;" in captured.err
    else:
        assert captured.err == ""


def test_explicit_context_stays_quiet(make_console, capsys):
    make_console()
    _print_context(
        [
            ("Owner", "owner", _ContextSource()),
            ("Project", "project-a", _ContextSource()),
            ("Run", "run-uuid", _ContextSource()),
        ]
    )

    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("ambient_show_context", [False, True])
def test_reporting_uses_explicit_argument(
    ambient_show_context, make_console, monkeypatch, capsys
):
    from polyaxon._cli.context import resolve_project
    from polyaxon._env_vars.getters.project import _ProjectContext

    make_console()
    source = _ContextSource("local cache", "/work/.polyaxon/.project")
    resolved = _ProjectContext("owner", None, "project", source, source)
    monkeypatch.setattr(
        "polyaxon._cli.context._get_project_context", lambda project, is_cli: resolved
    )
    with click.Context(
        click.Command("test"), obj={"show_context": ambient_show_context}
    ):
        assert resolve_project(show_context=False) == ("owner", None, "project")
        captured = capsys.readouterr()
        assert captured.out == captured.err == ""

        assert resolve_project(show_context=True) == ("owner", None, "project")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.count("Context:") == 1
        assert source.path in captured.err


@pytest.mark.parametrize("is_cli", [False, True])
def test_getters_resolve_without_reporting(
    is_cli, tmp_path, monkeypatch, capsys, caplog
):
    from polyaxon._env_vars.getters import get_local_owner
    from polyaxon._env_vars.getters.project import _get_project_context
    from polyaxon._env_vars.getters.run import _get_project_run_context
    from polyaxon._managers.project import ProjectConfigManager
    from polyaxon._managers.run import RunConfigManager
    from polyaxon._managers.user import UserConfigManager
    from polyaxon._sdk.schemas.v1_project import V1Project
    from polyaxon._sdk.schemas.v1_run import V1Run
    from polyaxon._sdk.schemas.v1_user import V1User

    caplog.set_level(logging.INFO, logger="polyaxon.cli")
    monkeypatch.chdir(tmp_path)
    for manager in (ProjectConfigManager, RunConfigManager, UserConfigManager):
        monkeypatch.setattr(manager, "CONFIG_PATH", str(tmp_path / "global"))
    UserConfigManager.set_config(V1User(organization="owner"))
    ProjectConfigManager.set_config(
        V1Project(owner="owner", name="project"), visibility="local"
    )
    run_uuid = "11111111111111111111111111111111"
    RunConfigManager.set_config(
        V1Run(uuid=run_uuid, owner="owner", project="project"), visibility="local"
    )

    with click.Context(click.Command("test"), obj={"show_context": True}):
        assert get_local_owner(is_cli=is_cli) == "owner"
        project_context = _get_project_context(is_cli=is_cli)
        assert (
            project_context.owner,
            project_context.team,
            project_context.project,
        ) == ("owner", None, "project")

        project_context, run_context = _get_project_run_context(is_cli=is_cli)
        assert (
            project_context.owner,
            project_context.team,
            project_context.project,
            run_context.uuid,
        ) == (
            "owner",
            None,
            "project",
            run_uuid,
        )

    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert "Using cached" not in caplog.text
