from typing import Dict, List, Optional, Union

from clipped.utils.query_params import get_query_params

from polyaxon._client.client import PolyaxonClient
from polyaxon._client.decorators import client_handler, get_global_or_inline_config
from polyaxon._client.mixin import ClientMixin
from polyaxon._constants.globals import DEFAULT
from polyaxon._env_vars.getters.user import get_local_owner
from polyaxon._schemas.lifecycle import V1ProjectVersionKind
from polyaxon._sdk.schemas.v1_entities_transfer import V1EntitiesTransfer
from polyaxon._sdk.schemas.v1_entities_tags import V1EntitiesTags
from polyaxon._sdk.schemas.v1_list_organization_members_response import (
    V1ListOrganizationMembersResponse,
)
from polyaxon._sdk.schemas.v1_list_project_versions_response import (
    V1ListProjectVersionsResponse,
)
from polyaxon._sdk.schemas.v1_list_run_artifacts_response import (
    V1ListRunArtifactsResponse,
)
from polyaxon._sdk.schemas.v1_list_organizations_response import (
    V1ListOrganizationsResponse,
)
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_list_teams_response import V1ListTeamsResponse
from polyaxon._sdk.schemas.v1_organization import V1Organization
from polyaxon._sdk.schemas.v1_organization_member import V1OrganizationMember
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_uuids import V1Uuids
from polyaxon._utils.fqn_utils import split_owner_team_space
from polyaxon.exceptions import PolyaxonClientException
from polyaxon.logger import logger


class OrganizationClient(ClientMixin):
    """OrganizationClient is a client to communicate with Polyaxon organizations endpoints.

    If no values are passed to this class,
    Polyaxon will try to resolve the owner from the environment:
     * If you have a configured CLI, Polyaxon will use the configuration of the cli.
     * If you use this client in the context of a job or a service managed by Polyaxon,
       a configuration will be available to resolve the values based on that run.

    Team Scoping (Using as a Team Client):
        This client can be used as a **Team Client** by providing the owner in the
        format "owner/team". When a team is specified, all applicable methods will
        operate within that team's scope rather than organization-wide.

        Team-scoped methods include:
            * Runs: list_runs, get_run, approve_runs, archive_runs, restore_runs,
              delete_runs, stop_runs, skip_runs, invalidate_runs, bookmark_runs,
              tag_runs, transfer_runs
            * Versions: list_versions, list_component_versions, list_model_versions,
              list_artifact_versions
            * Artifacts: list_runs_artifacts_lineage

        Examples:
            # Organization-wide operations
            org_client = OrganizationClient(owner="my-org")
            org_client.list_runs()  # All runs across the organization

            # Team-scoped operations (effectively a "Team Client")
            team_client = OrganizationClient(owner="my-org/engineering")
            team_client.list_runs()  # Only runs within the engineering team
            team_client.list_model_versions()  # Only model versions within the team

    Properties:
        owner: str.
        team: str.
        organization_data: V1Organization.

    Args:
        owner: str, optional, the owner is the username or the organization name.
               Can be specified as "owner" for organization-wide scope or "owner/team"
               for team-scoped operations.
        client: [PolyaxonClient](/docs/core/python-library/polyaxon-client/), optional,
             an instance of a configured client, if not passed,
             a new instance will be created based on the available environment.
        is_offline: bool, optional,
             To trigger the offline mode manually instead of depending on `POLYAXON_IS_OFFLINE`.
        no_op: bool, optional,
             To set the NO_OP mode manually instead of depending on `POLYAXON_NO_OP`.

    Raises:
        PolyaxonClientException: If no owner is passed and Polyaxon cannot
            resolve an owner from the environment.
    """

    @client_handler(check_no_op=True)
    def __init__(
        self,
        owner: Optional[str] = None,
        client: Optional[PolyaxonClient] = None,
        is_offline: Optional[bool] = None,
        no_op: Optional[bool] = None,
        manual_exceptions_handling: bool = False,
    ):
        self._manual_exceptions_handling = manual_exceptions_handling
        self._is_offline = get_global_or_inline_config(
            config_key="is_offline", config_value=is_offline, client=client
        )
        self._no_op = get_global_or_inline_config(
            config_key="no_op", config_value=no_op, client=client
        )

        if self._no_op:
            return

        if not owner:
            owner = get_local_owner()
        if not owner:
            raise PolyaxonClientException("Please provide a valid owner.")

        owner, team = split_owner_team_space(owner)
        self._client = client
        self._owner = owner or DEFAULT
        self._team = team
        self._organization_data = V1Organization.model_construct()

    @property
    def organization_data(self):
        return self._organization_data

    @client_handler(check_no_op=True, check_offline=True)
    def refresh_data(self):
        """Fetches the organization data from the api."""
        self._organization_data = self.client.organizations_v1.get_organization(
            self.owner
        )
        if self._organization_data.name is None:
            self._organization_data.name = self.owner

    @client_handler(check_no_op=True, check_offline=True)
    def list(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListOrganizationsResponse:
        """Lists organizations.

        [Organization API](/docs/api/#operation/ListOrganizations)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of organizations to return.
            offset: int, optional, offset pages to paginate organizations.

        Returns:
            V1ListOrganizationsResponse, list of organization instances.
        """
        params = get_query_params(limit=limit, offset=offset, query=query, sort=sort)
        return self.client.organizations_v1.list_organizations(**params)

    # Organization Members Management
    @client_handler(check_no_op=True, check_offline=True)
    def list_members(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListOrganizationMembersResponse:
        """Lists organization members.

        [Organization API](/docs/api/#operation/ListOrganizationMembers)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of members to return.
            offset: int, optional, offset pages to paginate members.

        Returns:
            V1ListOrganizationMembersResponse, list of organization member instances.
        """
        params = get_query_params(
            limit=limit or 20, offset=offset, query=query, sort=sort
        )
        return self.client.organizations_v1.list_organization_members(
            self.owner, **params
        )

    @client_handler(check_no_op=True, check_offline=True)
    def get_member(self, user: str) -> V1OrganizationMember:
        """Gets an organization member.

        [Organization API](/docs/api/#operation/GetOrganizationMember)

        Args:
            user: str, required, the username of the member.

        Returns:
            V1OrganizationMember, organization member instance.
        """
        return self.client.organizations_v1.get_organization_member(self.owner, user)

    @client_handler(check_no_op=True, check_offline=True)
    def create_member(
        self,
        data: Union[Dict, V1OrganizationMember],
        email: Optional[str] = None,
    ) -> V1OrganizationMember:
        """Creates a new organization member.

        [Organization API](/docs/api/#operation/CreateOrganizationMember)

        Args:
            data: Dict or V1OrganizationMember, required.
            email: str, optional, email of the member to invite.

        Returns:
            V1OrganizationMember, organization member instance from the response.
        """
        return self.client.organizations_v1.create_organization_member(
            self.owner,
            body=data,
            email=email,
            async_req=False,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def update_member(
        self,
        user: str,
        data: Union[Dict, V1OrganizationMember],
    ) -> V1OrganizationMember:
        """Updates an organization member based on the data passed.

        [Organization API](/docs/api/#operation/UpdateOrganizationMember)

        Args:
            user: str, required, the username of the member.
            data: Dict or V1OrganizationMember, required.

        Returns:
            V1OrganizationMember, organization member instance from the response.
        """
        return self.client.organizations_v1.update_organization_member(
            self.owner,
            user,
            body=data,
            async_req=False,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def patch_member(
        self,
        user: str,
        data: Union[Dict, V1OrganizationMember],
    ) -> V1OrganizationMember:
        """Patches an organization member based on the data passed.

        [Organization API](/docs/api/#operation/PatchOrganizationMember)

        Args:
            user: str, required, the username of the member.
            data: Dict or V1OrganizationMember, required.

        Returns:
            V1OrganizationMember, organization member instance from the response.
        """
        return self.client.organizations_v1.patch_organization_member(
            self.owner,
            user,
            body=data,
            async_req=False,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def delete_member(self, user: str):
        """Deletes an organization member.

        [Organization API](/docs/api/#operation/DeleteOrganizationMember)

        Args:
            user: str, required, the username of the member.
        """
        return self.client.organizations_v1.delete_organization_member(self.owner, user)

    # Organization Teams Management
    @client_handler(check_no_op=True, check_offline=True)
    def list_teams(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        bookmarks: bool = False,
        mode: Optional[str] = None,
    ) -> V1ListTeamsResponse:
        """Lists teams in the organization.

        [Teams API](/docs/api/#operation/ListTeams)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of teams to return.
            offset: int, optional, offset pages to paginate teams.
            bookmarks: bool, optional, filter by bookmarks.
            mode: str, optional, mode of the search.
        Returns:
            V1ListTeamsResponse, list of team instances.
        """
        params = get_query_params(
            limit=limit or 20, offset=offset, query=query, sort=sort
        )
        if bookmarks:
            params["bookmarks"] = bookmarks
        if mode:
            params["mode"] = mode
        return self.client.teams_v1.list_teams(self.owner, **params)

    # Organization Runs Management
    @client_handler(check_no_op=True, check_offline=True)
    def list_runs(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListRunsResponse:
        """Lists runs across all projects in the organization or team.

        [Organization API](/docs/api/#operation/GetOrganizationRuns)
        [Team API](/docs/api/#operation/GetTeamRuns)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of runs to return.
            offset: int, optional, offset pages to paginate runs.

        Returns:
            V1ListRunsResponse, list of run instances.
        """
        params = get_query_params(
            limit=limit or 20, offset=offset, query=query, sort=sort
        )
        if self.team:
            return self.client.teams_v1.get_team_runs(self.owner, self.team, **params)
        return self.client.organizations_v1.get_organization_runs(self.owner, **params)

    @client_handler(check_no_op=True, check_offline=True)
    def get_run(self, uuid: str) -> V1Run:
        """Gets a run by uuid from the organization or team.

        [Organization API](/docs/api/#operation/GetOrganizationRun)
        [Team API](/docs/api/#operation/GetTeamRun)

        Args:
            uuid: str, required, the run uuid.

        Returns:
            V1Run, run instance.
        """
        if self.team:
            return self.client.teams_v1.get_team_run(self.owner, self.team, uuid)
        return self.client.organizations_v1.get_organization_run(self.owner, uuid)

    @client_handler(check_no_op=True, check_offline=True)
    def approve_runs(self, uuids: Union[List[str], V1Uuids]):
        """Approves multiple runs in the organization.

        [Organization API](/docs/api/#operation/ApproveOrganizationRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to approve.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.approve_team_runs(self.owner, self.team, uuids)
        return self.client.organizations_v1.approve_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def archive_runs(self, uuids: Union[List[str], V1Uuids]):
        """Archives multiple runs in the organization.

        [Organization API](/docs/api/#operation/ArchiveOrganizationRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to archive.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.archive_team_runs(self.owner, self.team, uuids)
        return self.client.organizations_v1.archive_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def restore_runs(self, uuids: Union[List[str], V1Uuids]):
        """Restores multiple runs in the organization.

        [Organization API](/docs/api/#operation/RestoreOrganizationRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to restore.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.restore_team_runs(self.owner, self.team, uuids)
        return self.client.organizations_v1.restore_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def delete_runs(self, uuids: Union[List[str], V1Uuids]):
        """Deletes multiple runs in the organization or team.

        [Organization API](/docs/api/#operation/DeleteOrganizationRuns)
        [Team API](/docs/api/#operation/DeleteTeamRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to delete.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        logger.info("Deleting {} runs".format(len(uuids.uuids)))
        if self.team:
            return self.client.teams_v1.delete_team_runs(
                self.owner, self.team, body=uuids
            )
        return self.client.organizations_v1.delete_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def stop_runs(self, uuids: Union[List[str], V1Uuids]):
        """Stops multiple runs in the organization or team.

        [Organization API](/docs/api/#operation/StopOrganizationRuns)
        [Team API](/docs/api/#operation/StopTeamRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to stop.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.stop_team_runs(
                self.owner, self.team, body=uuids
            )
        return self.client.organizations_v1.stop_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def skip_runs(self, uuids: Union[List[str], V1Uuids]):
        """Skips multiple runs in the organization.

        [Organization API](/docs/api/#operation/SkipOrganizationRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to skip.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.skip_team_runs(
                self.owner, self.team, body=uuids
            )
        return self.client.organizations_v1.skip_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def invalidate_runs(self, uuids: Union[List[str], V1Uuids]):
        """Invalidates multiple runs in the organization or team.

        [Organization API](/docs/api/#operation/InvalidateOrganizationRuns)
        [Team API](/docs/api/#operation/InvalidateTeamRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to invalidate.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.invalidate_team_runs(
                self.owner, self.team, body=uuids
            )
        return self.client.organizations_v1.invalidate_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def bookmark_runs(self, uuids: Union[List[str], V1Uuids]):
        """Bookmarks multiple runs in the organization.

        [Organization API](/docs/api/#operation/BookmarkOrganizationRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to bookmark.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        if self.team:
            return self.client.teams_v1.bookmark_team_runs(
                self.owner, self.team, body=uuids
            )
        return self.client.organizations_v1.bookmark_organization_runs(
            self.owner, body=uuids
        )

    @client_handler(check_no_op=True, check_offline=True)
    def tag_runs(self, uuids: Union[List[str], V1Uuids], tags: List[str]):
        """Tags multiple runs in the organization.

        [Organization API](/docs/api/#operation/TagOrganizationRuns)

        Args:
            data: Dict, required, must include 'uuids' and 'tags' fields.
        """
        if isinstance(uuids, list):
            uuids = V1Uuids(uuids=uuids)
        data = V1EntitiesTags(
            uuids=uuids.uuids,
            tags=tags,
        )
        if self.team:
            return self.client.teams_v1.tag_team_runs(self.owner, self.team, body=data)
        return self.client.organizations_v1.tag_organization_runs(self.owner, body=data)

    @client_handler(check_no_op=True, check_offline=True)
    def transfer_runs(
        self,
        uuids: Union[List[str], V1Uuids],
        to_project: str,
    ):
        """Transfers multiple runs to another project in the organization.

        [Organization API](/docs/api/#operation/TransferOrganizationRuns)

        Args:
            uuids: List[str] or V1Uuids, required, list of run uuids to transfer.
            to_project: str, required, the destination project to transfer the runs to.
        """
        if isinstance(uuids, list):
            transfer_data = V1EntitiesTransfer(uuids=uuids, project=to_project)
        else:
            transfer_data = V1EntitiesTransfer(uuids=uuids.uuids, project=to_project)

        logger.info(
            "Transferring {} runs to project {}".format(
                len(transfer_data.uuids), to_project
            )
        )
        if self.team:
            return self.client.teams_v1.transfer_team_runs(
                self.owner, self.team, body=transfer_data
            )
        return self.client.organizations_v1.transfer_organization_runs(
            self.owner, body=transfer_data
        )

    # Organization Versions Management
    def _validate_kind(self, kind: V1ProjectVersionKind):
        """Validates that the version kind is valid."""
        if kind not in V1ProjectVersionKind.to_set():
            raise ValueError(
                "The kind `{}` is not supported, it must be one of the values `{}`".format(
                    kind, V1ProjectVersionKind.to_list()
                )
            )

    @client_handler(check_no_op=True, check_offline=True)
    def list_versions(
        self,
        kind: V1ProjectVersionKind,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListProjectVersionsResponse:
        """Lists project versions across all projects in the organization or team.

        This is a generic function that lists versions of a specific kind
        across all projects in the organization or team:
            * component versions
            * model versions
            * artifact versions

        [Organization API](/docs/api/#operation/GetOrganizationVersions)
        [Team API](/docs/api/#operation/GetTeamVersions)

        Args:
            kind: V1ProjectVersionKind, kind of the project version.
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of versions to return.
            offset: int, optional, offset pages to paginate versions.

        Returns:
            V1ListProjectVersionsResponse, list of project versions across all projects.
        """
        self._validate_kind(kind)
        params = get_query_params(
            limit=limit or 20, offset=offset, query=query, sort=sort
        )
        if self.team:
            return self.client.teams_v1.get_team_versions(
                self.owner, self.team, kind, **params
            )
        return self.client.organizations_v1.get_organization_versions(
            self.owner, kind, **params
        )

    @client_handler(check_no_op=True, check_offline=True)
    def list_component_versions(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListProjectVersionsResponse:
        """Lists component versions across all projects in the organization or team.

        [Organization API](/docs/api/#operation/GetOrganizationVersions)
        [Team API](/docs/api/#operation/GetTeamVersions)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of versions to return.
            offset: int, optional, offset pages to paginate versions.

        Returns:
            V1ListProjectVersionsResponse, list of component versions.
        """
        return self.list_versions(
            kind=V1ProjectVersionKind.COMPONENT,
            query=query,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def list_model_versions(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListProjectVersionsResponse:
        """Lists model versions across all projects in the organization or team.

        [Organization API](/docs/api/#operation/GetOrganizationVersions)
        [Team API](/docs/api/#operation/GetTeamVersions)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of versions to return.
            offset: int, optional, offset pages to paginate versions.

        Returns:
            V1ListProjectVersionsResponse, list of model versions.
        """
        return self.list_versions(
            kind=V1ProjectVersionKind.MODEL,
            query=query,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def list_artifact_versions(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> V1ListProjectVersionsResponse:
        """Lists artifact versions across all projects in the organization or team.

        [Organization API](/docs/api/#operation/GetOrganizationVersions)
        [Team API](/docs/api/#operation/GetTeamVersions)

        Args:
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of versions to return.
            offset: int, optional, offset pages to paginate versions.

        Returns:
            V1ListProjectVersionsResponse, list of artifact versions.
        """
        return self.list_versions(
            kind=V1ProjectVersionKind.ARTIFACT,
            query=query,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    @client_handler(check_no_op=True, check_offline=True)
    def list_runs_artifacts_lineage(
        self,
        name: Optional[str] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        bookmarks: bool = False,
        mode: Optional[str] = None,
    ) -> V1ListRunArtifactsResponse:
        """Lists artifact lineage for runs across all projects in the organization.

        [Organization API](/docs/api/#operation/GetOrganizationRunsArtifactsLineage)

        Args:
            name: str, optional, entity name filter.
            query: str, optional, query filters
            sort: str, optional, fields to order by
            limit: int, optional, limit of artifacts to return.
            offset: int, optional, offset pages to paginate artifacts.
            bookmarks: bool, optional, filter by bookmarks.
            mode: str, optional, mode of the search.

        Returns:
            V1ListRunArtifactsResponse, list of run artifacts with lineage info.
        """
        params = get_query_params(
            limit=limit or 20, offset=offset, query=query, sort=sort
        )
        if name:
            params["name"] = name
        if bookmarks:
            params["bookmarks"] = bookmarks
        if mode:
            params["mode"] = mode

        if self.team:
            return self.client.teams_v1.get_team_runs_artifacts_lineage(
                self.owner, self.team, **params
            )
        return self.client.organizations_v1.get_organization_runs_artifacts_lineage(
            self.owner, **params
        )
