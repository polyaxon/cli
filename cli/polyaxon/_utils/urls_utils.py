from typing import Optional
from urllib.parse import urljoin


def get_owner_url(owner: str) -> str:
    return "/{}".format(owner)


def get_project_url(unique_name: str) -> str:
    values = unique_name.split(".")
    return "{}/{}".format(get_owner_url(values[0]), values[1])


def get_owner_project_url(owner: str, project_name: str) -> str:
    return "{}/{}".format(get_owner_url(owner), project_name)


def get_fqn_run_url(unique_name: str) -> str:
    values = unique_name.split(".")
    project_url = get_owner_project_url(owner=values[0], project_name=values[1])
    return f"{project_url}/runs/{values[-1]}"


def get_run_url(owner: str, project_name: str, run_uuid: str) -> str:
    project_url = get_owner_project_url(owner=owner, project_name=project_name)
    return f"{project_url}/runs/{run_uuid}"


def get_run_health_url(unique_name: str) -> str:
    run_url = get_fqn_run_url(unique_name=unique_name)
    return f"{run_url}/_heartbeat"


def get_proxy_run_url(
    service: str,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    subpath: Optional[str] = None,
    port: Optional[int] = None,
) -> str:
    url_path = "{namespace}/{owner}/{project}/runs/{run_uuid}".format(
        namespace=namespace,
        owner=owner,
        project=project,
        run_uuid=run_uuid,
    )
    if port:
        url_path = "{}/{}".format(url_path, port)
    if subpath:
        url_path = "{}/{}".format(url_path, subpath)
    return urljoin(service.rstrip() + "/", url_path.lstrip("/"))


def get_run_reconcile_url(unique_name: str) -> str:
    run_url = get_fqn_run_url(unique_name=unique_name)
    return "{}/_reconcile".format(run_url)


URL_FORMAT = "{protocol}://{domain}{path}"
