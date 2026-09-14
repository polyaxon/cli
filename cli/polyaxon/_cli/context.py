from typing import Optional, Sequence, Tuple

from clipped.formatting import Printer
from polyaxon._client.decorators import get_global_or_inline_config
from polyaxon._env_vars.getters._context import _ContextSource
from polyaxon._env_vars.getters.project import _get_project_context
from polyaxon._env_vars.getters.run import _get_project_run_context, _RunContext
from polyaxon._env_vars.getters.user import _get_local_owner_context


def resolve_owner(is_cli: bool = True, *, show_context: bool):
    owner, source = _get_local_owner_context(is_cli=is_cli)
    if show_context:
        _print_context([("Owner", owner, source)])
    return owner


def resolve_project(project=None, is_cli: bool = True, *, show_context: bool):
    context = _get_project_context(project, is_cli=is_cli)
    if show_context:
        _print_context(context.fields())
    return context.owner, context.team, context.project


def resolve_run(
    project=None, run_uuid=None, is_cli: bool = True, *, show_context: bool
):
    project_context, run_context = _get_project_run_context(
        project, run_uuid, is_cli=is_cli
    )
    if show_context:
        _print_context(
            project_context.fields() + [("Run", run_context.uuid, run_context.source)],
            incomplete_run=run_context.incomplete,
        )
    return (
        project_context.owner,
        project_context.team,
        project_context.project,
        run_context.uuid,
    )


def report_client_context(client, include_run: bool = False, *, show_context: bool):
    if not show_context:
        return

    context = _get_client_context(client, include_run=include_run)
    if context is None:
        return

    fields, incomplete_run = context
    _print_context(fields, incomplete_run=incomplete_run)


def _get_client_context(client, include_run: bool = False):
    if get_global_or_inline_config(
        config_key="no_op",
        config_value=getattr(client, "_no_op", None),
        client=getattr(client, "_client", None),
    ):
        return None

    project_context = client._project_context_snapshot()
    fields = project_context.fields()
    incomplete_run = False
    if include_run and not client._is_offline:
        context = client._run_context or _RunContext(uuid=client._run_uuid)
        context.validate(project_context)
        fields.append(("Run", client._run_uuid, context.source))
        incomplete_run = context.incomplete
    return fields, incomplete_run


def _print_context(
    fields: Sequence[Tuple[str, Optional[str], _ContextSource]],
    incomplete_run: bool = False,
):
    if not any(value is not None and source.path for _, value, source in fields):
        return

    from rich.text import Text

    context = {}
    for name, value, source in fields:
        if value is not None:
            context[name] = Text.assemble(
                (value, "bold"), "  ", (source.describe(), "dim"), overflow="fold"
            )

    Printer.header("Context:", err=True)
    Printer.dict_tabulate(context, err=True)
    if incomplete_run:
        Printer.warning(
            "Cached owner/project metadata is incomplete; "
            "only known ownership fields were checked.",
            err=True,
            markup=False,
        )
