import os
import sys

from typing import Callable, List, Optional, Union

import click

from clipped.formatting import Printer
from clipped.utils.dicts import dict_to_tabulate, list_dicts_to_tabulate
from clipped.utils.query_params import get_query_params
from clipped.utils.responses import get_meta_response
from clipped.utils.validation import validate_tags
from urllib3.exceptions import HTTPError

from polyaxon._cli.dashboard import get_dashboard_url
from polyaxon._cli.errors import handle_cli_error
from polyaxon._contexts.paths import get_offline_base_path
from polyaxon._schemas.lifecycle import V1ProjectVersionKind
from polyaxon._utils.fqn_utils import get_versioned_entity_full_name
from polyaxon.client import PolyaxonClient, ProjectClient
from polyaxon.exceptions import ApiException


def get_version_details(response, content_callback: Callable = None):
    content = response.content
    meta_info = response.meta_info
    readme = response.readme
    response = dict_to_tabulate(
        response.to_dict(),
        humanize_values=True,
        exclude_attrs=["content", "meta_info", "stage_conditions", "readme"],
    )

    Printer.heading("Version info:")
    Printer.dict_tabulate(response)

    if meta_info:
        artifacts = meta_info.pop("artifacts", None)
        lineage = meta_info.pop("lineage", artifacts)
        if meta_info:
            Printer.heading("Version meta info:")
            Printer.dict_tabulate(meta_info)

        if lineage:
            Printer.heading("Version artifacts lineage:")
            Printer.print_json(lineage)

    if readme:
        Printer.heading("Version readme:")
        Printer.print_md(readme)

    def get_content(_content: str):
        if _content:
            Printer.heading("Content:")
            Printer.print_yaml(_content)

    content_callback = content_callback or get_content
    content_callback(content)


def get_version_stages_table(stage, conditions):
    table = Printer.get_table()

    if not conditions:
        Printer.print(table)
        return

    Printer.print(
        "Latest stage: {}".format(
            Printer.add_status_color({"stage": stage}, status_key="stage")["stage"]
        )
    )
    objects = [
        dict_to_tabulate(Printer.add_status_color(o.to_dict(), status_key="type"))
        for o in conditions
    ]

    if not objects:
        Printer.print(table)
        return

    if not table.columns:
        for c in objects[0].keys():
            table.add_column(c)
    if objects:
        for o in objects:
            table.add_row(*o.values())

    Printer.print(table)


def list_project_versions_response(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    query: Optional[str] = None,
    sort: Optional[str] = None,
    client: Optional[PolyaxonClient] = None,
):
    polyaxon_client = ProjectClient(
        owner=owner,
        project=project_name,
        client=client,
        manual_exceptions_handling=True,
    )
    params = get_query_params(limit=limit, offset=offset, query=query, sort=sort)
    try:
        return polyaxon_client.list_versions(kind=kind, **params)
    except (ApiException, HTTPError) as e:
        message = "Could not get list of {} versions for {}/{}.".format(
            kind, owner, project_name
        )
        handle_cli_error(e, message=message)
        sys.exit(1)


def list_project_versions(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    limit: Optional[str] = None,
    offset: Optional[str] = None,
    query: Optional[str] = None,
    sort: Optional[str] = None,
    client: Optional[PolyaxonClient] = None,
):
    version_info = "<owner: {}> <project: {}>".format(owner, project_name)
    response = list_project_versions_response(
        owner=owner,
        project_name=project_name,
        kind=kind,
        limit=limit,
        offset=offset,
        query=query,
        sort=sort,
        client=client,
    )
    meta = get_meta_response(response)
    if meta:
        Printer.heading("Versions for {}".format(version_info))
        Printer.heading("Navigation:")
        Printer.dict_tabulate(meta)
    else:
        Printer.header("No version found for {}".format(version_info))

    objects = list_dicts_to_tabulate(
        [o.to_dict() for o in response.results],
        humanize_values=True,
        exclude_attrs=[
            "uuid",
            "readme",
            "description",
            "owner",
            "project",
            "role",
            "content",
            "connection",
            "meta_info",
            "run",
            "artifacts",
            "stage_conditions",
        ],
    )
    if objects:
        Printer.heading("Versions:")
        Printer.dict_tabulate(objects, is_list_dict=True)


def register_project_version(
    owner: str,
    project_name: str,
    version: str,
    kind: V1ProjectVersionKind,
    description: Optional[str] = None,
    tags: Optional[Union[str, List[str]]] = None,
    content: Optional[str] = None,
    run: Optional[str] = None,
    connection: Optional[str] = None,
    artifacts: Optional[Union[str, List[str]]] = None,
    force: bool = False,
):
    version = version or "latest"
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    try:
        _version = polyaxon_client.register_version(
            kind=kind,
            version=version,
            description=description,
            tags=tags,
            content=content,
            run=run,
            connection=connection,
            artifacts=artifacts,
            force=force,
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e, message="Could not create version `{}`.".format(fqn_version)
        )
        sys.exit(1)

    Printer.success("Version `{}` was created successfully.".format(fqn_version))
    Printer.print(
        "You can view this version on Polyaxon UI: {}".format(
            get_dashboard_url(
                subpath="{}/{}/{}s/{}".format(owner, project_name, kind, version)
            )
        )
    )


def copy_project_version(
    owner: str,
    project_name: str,
    version: str,
    kind: V1ProjectVersionKind,
    to_project: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[Union[str, List[str]]] = None,
    content: Optional[str] = None,
    force: bool = False,
):
    version = version or "latest"
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    try:
        _version = polyaxon_client.copy_version(
            kind=kind,
            version=version,
            to_project=to_project,
            name=name,
            description=description,
            tags=tags,
            content=content,
            force=force,
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not copy version `{}`.".format(fqn_version))
        sys.exit(1)

    fqn_copied_version = get_versioned_entity_full_name(
        owner,
        to_project or project_name,
        _version.name,
    )
    Printer.success(
        "Version `{}` was copied successfully to `{}`.".format(
            fqn_version, fqn_copied_version
        )
    )
    Printer.print(
        "You can view this version on Polyaxon UI: {}".format(
            get_dashboard_url(
                subpath="{}/{}/{}s/{}".format(
                    owner, to_project or project_name, kind, _version.name
                )
            )
        )
    )


def get_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    content_callback: Callable = None,
    client: Optional[PolyaxonClient] = None,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner,
        project=project_name,
        client=client,
        manual_exceptions_handling=True,
    )

    try:
        response = polyaxon_client.get_version(kind, version)
        get_version_details(response, content_callback)
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not get {} version `{}`.".format(
                kind,
                fqn_version,
            ),
            sys_exit=True,
        )


def get_project_version_stages(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    client: Optional[PolyaxonClient] = None,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner,
        project=project_name,
        client=client,
        manual_exceptions_handling=True,
    )

    try:
        stage, stage_conditions = polyaxon_client.get_version_stages(kind, version)
        get_version_stages_table(stage, stage_conditions)
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not get {} version `{}`.".format(
                kind,
                fqn_version,
            ),
            sys_exit=True,
        )


def delete_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    yes: bool = False,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    if not yes and not click.confirm(
        "Are sure you want to delete {} version `{}`".format(kind, fqn_version)
    ):
        Printer.print("Exiting without deleting {} version.".format(kind))
        sys.exit(1)

    try:
        polyaxon_client.delete_version(kind, version)
        Printer.success(
            "The {} version `{}` was delete successfully".format(kind, fqn_version)
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not delete the {} version `{}`.".format(kind, fqn_version),
        )
        sys.exit(1)


def update_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[Union[str, List[str]]] = None,
    content_callback: Callable = None,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    update_dict = {}
    if name:
        update_dict["name"] = name

    if description:
        update_dict["description"] = description

    tags = validate_tags(tags, validate_yaml=True)
    if tags:
        update_dict["tags"] = tags

    if not update_dict:
        Printer.warning(
            "No argument was provided to update the {} version {}.".format(
                kind, fqn_version
            )
        )
        sys.exit(1)

    try:
        response = polyaxon_client.patch_version(kind, version, update_dict)
        Printer.success("The {} version updated.".format(kind))
        get_version_details(response, content_callback)
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not update the {} version `{}`.".format(kind, fqn_version),
        )
        sys.exit(1)


def transfer_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    to_project: str,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    try:
        polyaxon_client.transfer_version(kind, version, to_project)
        Printer.success(
            "The `{}` version was transferred to `{}`.".format(kind, to_project)
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not transfer the {} version `{}` to `{}`.".format(
                kind, fqn_version, to_project
            ),
        )
        sys.exit(1)


def stage_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    to: str,
    reason: Optional[str] = None,
    message: Optional[str] = None,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    if not to:
        Printer.warning(
            "No argument was provided to update the version stage, "
            "please provide a correct `--to` value."
        )
        sys.exit(1)

    try:
        polyaxon_client.stage_version(
            kind, version, stage=to, reason=reason or "CliStageUpdate", message=message
        )
        Printer.success("The {} version's stage was updated.".format(kind))
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not update the stage for {} version `{}`.".format(
                kind, fqn_version
            ),
        )
        sys.exit(1)


def open_project_version_dashboard(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    url: str,
    yes: bool = False,
):
    subpath = "{}/{}/{}s/{}".format(owner, project_name, kind, version)

    artifact_url = get_dashboard_url(subpath=subpath)
    if url:
        Printer.header("The dashboard is available at: {}".format(artifact_url))
        sys.exit(0)
    if yes or click.confirm(
        "Dashboard page will now open in your browser. Continue?",
        default=True,
    ):
        click.launch(artifact_url)


def pull_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    path: str,
    download_artifacts: bool = True,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    try:
        Printer.header(
            "Pulling {} version [white]`{}`[/white] ...".format(kind, fqn_version),
        )
        path = polyaxon_client.pull_version(
            kind,
            version,
            path=path,
            download_artifacts=download_artifacts,
        )
        Printer.success(
            "Finished pulling the {} version `{}` to `{}`".format(
                kind, fqn_version, path
            )
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not pull the {} version `{}`".format(kind, fqn_version),
        )


def pull_one_or_many_project_versions(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: Optional[str] = None,
    all_versions: Optional[bool] = None,
    query: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    path: Optional[str] = None,
    download_artifacts: bool = True,
):
    def _pull(version_name: str):
        pull_project_version(
            owner=owner,
            project_name=project_name,
            kind=kind,
            version=version_name,
            path=path,
            download_artifacts=download_artifacts,
        )

    if all_versions or any([query, limit, offset]):
        limit = 1000 if all_versions else limit
        versions = list_project_versions_response(
            owner=owner,
            project_name=project_name,
            kind=kind,
            limit=limit,
            offset=offset,
            query=query,
        ).results
        Printer.header(f"Pulling {kind} versions (total: {len(versions)}) ...")
        for idx, version in enumerate(versions):
            Printer.heading(f"Pulling version {idx + 1}/{len(versions)} ...")
            _pull(version.name)
    elif version:
        _pull(version)
    else:
        Printer.error(
            "Please provide a version name, provide a query to filter versions to pull, "
            "or pass the flag `-a/--all` to pull versions.",
            sys_exit=True,
        )


def push_project_version(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    version: str,
    path: str,
    reset_project: bool = False,
    force: bool = False,
    clean: bool = False,
    sys_exit: bool = False,
):
    fqn_version = get_versioned_entity_full_name(owner, project_name, version)
    polyaxon_client = ProjectClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    try:
        try:
            polyaxon_client.load_offline_version(
                kind=kind,
                version=version,
                path=path,
                project_client=polyaxon_client,
                reset_project=reset_project,
                raise_if_not_found=True,
            )
        except Exception as _:
            Printer.error(
                "Could not load offline version `{}`.".format(version),
                sys_exit=sys_exit,
            )
            return

        Printer.header(
            "Pushing {} version [white]`{}`[/white] ...".format(kind, fqn_version),
        )
        polyaxon_client.push_version(
            kind,
            version,
            path=path,
            force=force,
            clean=clean,
        )
        Printer.success(
            "Finished pushing the {} version `{}` from `{}`".format(
                kind, fqn_version, path
            )
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e,
            message="Could not push the {} version `{}`".format(kind, fqn_version),
        )


def push_one_or_many_project_versions(
    owner: str,
    project_name: str,
    kind: V1ProjectVersionKind,
    path: str,
    version: Optional[str] = None,
    all_versions: Optional[bool] = None,
    reset_project: bool = False,
    force: bool = False,
    clean: bool = False,
):
    def _push(version_name: str):
        push_project_version(
            owner=owner,
            project_name=project_name,
            kind=kind,
            version=version_name,
            path=path,
            reset_project=reset_project,
            force=force,
            clean=clean,
        )

    offline_path = get_offline_base_path(
        entity_kind=kind,
        path=path,
    )

    if all_versions:
        if (
            not os.path.exists(offline_path)
            or not os.path.isdir(offline_path)
            or not os.listdir(offline_path)
        ):
            Printer.error(
                f"Could not push offline {kind} versions, the path `{offline_path}` "
                f"does not exist, is not a directory, or is empty."
            )
            sys.exit(1)
        version_paths = os.listdir(offline_path)
        Printer.header(
            f"Pushing local {kind} versions (total: {len(version_paths)}) ..."
        )
        for idx, uid in enumerate(version_paths):
            Printer.heading(f"Pushing {kind} version {idx + 1}/{len(offline_path)} ...")
            _push(uid)
    elif version:
        _push(version)
    else:
        Printer.error(
            "Please provide a version name, or pass the flag `-a/--all` to pull versions.",
            sys_exit=True,
        )
