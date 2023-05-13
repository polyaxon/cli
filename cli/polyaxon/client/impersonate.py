from typing import Optional

from urllib3.exceptions import HTTPError

from polyaxon.client.client import PolyaxonClient
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonClientException
from polyaxon.schemas.api.authentication import AccessTokenConfig
from polyaxon.sdk.exceptions import ApiException


def create_context_auth(
    access_token: AccessTokenConfig, context_auth_path: Optional[str] = None
):
    context_auth_path = context_auth_path or ctx_paths.CONTEXT_MOUNT_AUTH
    with open(context_auth_path, "w") as config_file:
        config_file.write(access_token.to_json())


def impersonate(
    owner: str, project: str, run_uuid: str, client: Optional[PolyaxonClient] = None
):
    try:
        client = client or PolyaxonClient()
        response = client.runs_v1.impersonate_token(owner, project, run_uuid)
        polyaxon_client = PolyaxonClient(token=response.token)
        user = polyaxon_client.users_v1.get_user()
        access_token = AccessTokenConfig.construct(
            username=user.username, token=response.token
        )
        create_context_auth(access_token)
    except (ApiException, HTTPError) as e:
        raise PolyaxonClientException(
            "This worker is not allowed to run this job %s." % e
        )
