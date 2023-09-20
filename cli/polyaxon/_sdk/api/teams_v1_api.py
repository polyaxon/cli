from typing import Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictInt, StrictStr, validate_arguments

from polyaxon._sdk.base_api import BaseApi
from polyaxon._sdk.schemas.v1_list_team_members_response import (
    V1ListTeamMembersResponse,
)
from polyaxon._sdk.schemas.v1_list_teams_response import V1ListTeamsResponse
from polyaxon._sdk.schemas.v1_team import V1Team
from polyaxon._sdk.schemas.v1_team_member import V1TeamMember
from polyaxon.exceptions import ApiTypeError


class TeamsV1Api(BaseApi):
    @validate_arguments
    def create_team(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        body: Annotated[V1Team, Field(..., description="Team body")],
        **kwargs
    ) -> V1Team:
        """Create team

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_team(owner, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param body: Team body (required)
        :type body: V1Team
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1Team
        """
        kwargs["_return_http_data_only"] = True
        return self.create_team_with_http_info(owner, body, **kwargs)

    @validate_arguments
    def create_team_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        body: Annotated[V1Team, Field(..., description="Team body")],
        **kwargs
    ):
        """Create team

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_team_with_http_info(owner, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param body: Team body (required)
        :type body: V1Team
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1Team, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "body"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method create_team" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None
        if _params["body"]:
            _body_params = _params["body"]

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["application/json"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]

        _response_types_map = {
            "200": "V1Team",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams",
            "POST",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def create_team_member(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team")],
        body: Annotated[V1TeamMember, Field(..., description="Team body")],
        **kwargs
    ) -> V1TeamMember:  # noqa: E501
        """Create team member  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_team_member(owner, team, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team (required)
        :type team: str
        :param body: Team body (required)
        :type body: V1TeamMember
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1TeamMember
        """
        kwargs["_return_http_data_only"] = True
        return self.create_team_member_with_http_info(
            owner, team, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def create_team_member_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team")],
        body: Annotated[V1TeamMember, Field(..., description="Team body")],
        **kwargs
    ):  # noqa: E501
        """Create team member  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_team_member_with_http_info(owner, team, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team (required)
        :type team: str
        :param body: Team body (required)
        :type body: V1TeamMember
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1TeamMember, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "team", "body"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method create_team_member" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team"]:
            _path_params["team"] = _params["team"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None
        if _params["body"]:
            _body_params = _params["body"]

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["application/json"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1TeamMember",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team}/members",
            "POST",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def delete_team(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Component under namesapce")],
        **kwargs
    ) -> None:  # noqa: E501
        """Delete team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_team(owner, name, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Component under namesapce (required)
        :type name: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.delete_team_with_http_info(owner, name, **kwargs)  # noqa: E501

    @validate_arguments
    def delete_team_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Component under namesapce")],
        **kwargs
    ):  # noqa: E501
        """Delete team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_team_with_http_info(owner, name, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Component under namesapce (required)
        :type name: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = ["owner", "name"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method delete_team" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["name"]:
            _path_params["name"] = _params["name"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{name}",
            "DELETE",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def delete_team_member(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team under namesapce")],
        user: Annotated[StrictStr, Field(..., description="Member under team")],
        **kwargs
    ) -> None:  # noqa: E501
        """Delete team member details  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_team_member(owner, team, user, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team under namesapce (required)
        :type team: str
        :param user: Member under team (required)
        :type user: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.delete_team_member_with_http_info(
            owner, team, user, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_team_member_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team under namesapce")],
        user: Annotated[StrictStr, Field(..., description="Member under team")],
        **kwargs
    ):  # noqa: E501
        """Delete team member details  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_team_member_with_http_info(owner, team, user, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team under namesapce (required)
        :type team: str
        :param user: Member under team (required)
        :type user: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = ["owner", "team", "user"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method delete_team_member" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team"]:
            _path_params["team"] = _params["team"]
        if _params["user"]:
            _path_params["user"] = _params["user"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team}/members/{user}",
            "DELETE",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def get_team(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Component under namesapce")],
        **kwargs
    ) -> V1Team:  # noqa: E501
        """Get team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_team(owner, name, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Component under namesapce (required)
        :type name: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1Team
        """
        kwargs["_return_http_data_only"] = True
        return self.get_team_with_http_info(owner, name, **kwargs)  # noqa: E501

    @validate_arguments
    def get_team_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Component under namesapce")],
        **kwargs
    ):  # noqa: E501
        """Get team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_team_with_http_info(owner, name, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Component under namesapce (required)
        :type name: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1Team, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "name"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_team" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["name"]:
            _path_params["name"] = _params["name"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1Team",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{name}",
            "GET",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def get_team_member(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team under namesapce")],
        user: Annotated[StrictStr, Field(..., description="Member under team")],
        **kwargs
    ) -> V1TeamMember:  # noqa: E501
        """Get team member details  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_team_member(owner, team, user, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team under namesapce (required)
        :type team: str
        :param user: Member under team (required)
        :type user: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1TeamMember
        """
        kwargs["_return_http_data_only"] = True
        return self.get_team_member_with_http_info(
            owner, team, user, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_team_member_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team under namesapce")],
        user: Annotated[StrictStr, Field(..., description="Member under team")],
        **kwargs
    ):  # noqa: E501
        """Get team member details  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_team_member_with_http_info(owner, team, user, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team under namesapce (required)
        :type team: str
        :param user: Member under team (required)
        :type user: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1TeamMember, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "team", "user"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_team_member" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team"]:
            _path_params["team"] = _params["team"]
        if _params["user"]:
            _path_params["user"] = _params["user"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1TeamMember",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team}/members/{user}",
            "GET",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def list_team_members(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[
            StrictStr, Field(..., description="Entity managing the resource")
        ],
        offset: Annotated[
            Optional[StrictInt], Field(description="Pagination offset.")
        ] = None,
        limit: Annotated[Optional[StrictInt], Field(description="Limit size.")] = None,
        sort: Annotated[
            Optional[StrictStr], Field(description="Sort to order the search.")
        ] = None,
        query: Annotated[
            Optional[StrictStr], Field(description="Query filter the search.")
        ] = None,
        bookmarks: Annotated[
            Optional[bool], Field(description="Filter by bookmarks.")
        ] = None,
        mode: Annotated[
            Optional[StrictStr], Field(description="Mode of the search.")
        ] = None,
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs
    ) -> V1ListTeamMembersResponse:  # noqa: E501
        """Get team members  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_team_members(owner, name, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity managing the resource (required)
        :type name: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
        :param bookmarks: Filter by bookmarks.
        :type bookmarks: bool
        :param mode: Mode of the search.
        :type mode: str
        :param no_page: No pagination.
        :type no_page: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1ListTeamMembersResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_team_members_with_http_info(
            owner, name, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_team_members_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[
            StrictStr, Field(..., description="Entity managing the resource")
        ],
        offset: Annotated[
            Optional[StrictInt], Field(description="Pagination offset.")
        ] = None,
        limit: Annotated[Optional[StrictInt], Field(description="Limit size.")] = None,
        sort: Annotated[
            Optional[StrictStr], Field(description="Sort to order the search.")
        ] = None,
        query: Annotated[
            Optional[StrictStr], Field(description="Query filter the search.")
        ] = None,
        bookmarks: Annotated[
            Optional[bool], Field(description="Filter by bookmarks.")
        ] = None,
        mode: Annotated[
            Optional[StrictStr], Field(description="Mode of the search.")
        ] = None,
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs
    ):  # noqa: E501
        """Get team members  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_team_members_with_http_info(owner, name, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity managing the resource (required)
        :type name: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
        :param bookmarks: Filter by bookmarks.
        :type bookmarks: bool
        :param mode: Mode of the search.
        :type mode: str
        :param no_page: No pagination.
        :type no_page: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1ListTeamMembersResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "name",
            "offset",
            "limit",
            "sort",
            "query",
            "bookmarks",
            "mode",
            "no_page",
        ]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method list_team_members" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["name"]:
            _path_params["name"] = _params["name"]

        # process the query parameters
        _query_params = []
        if _params.get("offset") is not None:  # noqa: E501
            _query_params.append(("offset", _params["offset"]))
        if _params.get("limit") is not None:  # noqa: E501
            _query_params.append(("limit", _params["limit"]))
        if _params.get("sort") is not None:  # noqa: E501
            _query_params.append(("sort", _params["sort"]))
        if _params.get("query") is not None:  # noqa: E501
            _query_params.append(("query", _params["query"]))
        if _params.get("bookmarks") is not None:  # noqa: E501
            _query_params.append(("bookmarks", _params["bookmarks"]))
        if _params.get("mode") is not None:  # noqa: E501
            _query_params.append(("mode", _params["mode"]))
        if _params.get("no_page") is not None:  # noqa: E501
            _query_params.append(("no_page", _params["no_page"]))

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1ListTeamMembersResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{name}/members",
            "GET",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def list_team_names(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        offset: Annotated[
            Optional[StrictInt], Field(description="Pagination offset.")
        ] = None,
        limit: Annotated[Optional[StrictInt], Field(description="Limit size.")] = None,
        sort: Annotated[
            Optional[StrictStr], Field(description="Sort to order the search.")
        ] = None,
        query: Annotated[
            Optional[StrictStr], Field(description="Query filter the search.")
        ] = None,
        bookmarks: Annotated[
            Optional[bool], Field(description="Filter by bookmarks.")
        ] = None,
        mode: Annotated[
            Optional[StrictStr], Field(description="Mode of the search.")
        ] = None,
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs
    ) -> V1ListTeamsResponse:  # noqa: E501
        """List teams names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_team_names(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
        :param bookmarks: Filter by bookmarks.
        :type bookmarks: bool
        :param mode: Mode of the search.
        :type mode: str
        :param no_page: No pagination.
        :type no_page: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1ListTeamsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_team_names_with_http_info(
            owner, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_team_names_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        offset: Annotated[
            Optional[StrictInt], Field(description="Pagination offset.")
        ] = None,
        limit: Annotated[Optional[StrictInt], Field(description="Limit size.")] = None,
        sort: Annotated[
            Optional[StrictStr], Field(description="Sort to order the search.")
        ] = None,
        query: Annotated[
            Optional[StrictStr], Field(description="Query filter the search.")
        ] = None,
        bookmarks: Annotated[
            Optional[bool], Field(description="Filter by bookmarks.")
        ] = None,
        mode: Annotated[
            Optional[StrictStr], Field(description="Mode of the search.")
        ] = None,
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs
    ):  # noqa: E501
        """List teams names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_team_names_with_http_info(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
        :param bookmarks: Filter by bookmarks.
        :type bookmarks: bool
        :param mode: Mode of the search.
        :type mode: str
        :param no_page: No pagination.
        :type no_page: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1ListTeamsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "offset",
            "limit",
            "sort",
            "query",
            "bookmarks",
            "mode",
            "no_page",
        ]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method list_team_names" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        # process the query parameters
        _query_params = []
        if _params.get("offset") is not None:  # noqa: E501
            _query_params.append(("offset", _params["offset"]))
        if _params.get("limit") is not None:  # noqa: E501
            _query_params.append(("limit", _params["limit"]))
        if _params.get("sort") is not None:  # noqa: E501
            _query_params.append(("sort", _params["sort"]))
        if _params.get("query") is not None:  # noqa: E501
            _query_params.append(("query", _params["query"]))
        if _params.get("bookmarks") is not None:  # noqa: E501
            _query_params.append(("bookmarks", _params["bookmarks"]))
        if _params.get("mode") is not None:  # noqa: E501
            _query_params.append(("mode", _params["mode"]))
        if _params.get("no_page") is not None:  # noqa: E501
            _query_params.append(("no_page", _params["no_page"]))

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1ListTeamsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/names",
            "GET",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def list_teams(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        offset: Annotated[
            Optional[StrictInt], Field(description="Pagination offset.")
        ] = None,
        limit: Annotated[Optional[StrictInt], Field(description="Limit size.")] = None,
        sort: Annotated[
            Optional[StrictStr], Field(description="Sort to order the search.")
        ] = None,
        query: Annotated[
            Optional[StrictStr], Field(description="Query filter the search.")
        ] = None,
        bookmarks: Annotated[
            Optional[bool], Field(description="Filter by bookmarks.")
        ] = None,
        mode: Annotated[
            Optional[StrictStr], Field(description="Mode of the search.")
        ] = None,
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs
    ) -> V1ListTeamsResponse:  # noqa: E501
        """List teams  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_teams(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
        :param bookmarks: Filter by bookmarks.
        :type bookmarks: bool
        :param mode: Mode of the search.
        :type mode: str
        :param no_page: No pagination.
        :type no_page: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1ListTeamsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_teams_with_http_info(
            owner, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_teams_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        offset: Annotated[
            Optional[StrictInt], Field(description="Pagination offset.")
        ] = None,
        limit: Annotated[Optional[StrictInt], Field(description="Limit size.")] = None,
        sort: Annotated[
            Optional[StrictStr], Field(description="Sort to order the search.")
        ] = None,
        query: Annotated[
            Optional[StrictStr], Field(description="Query filter the search.")
        ] = None,
        bookmarks: Annotated[
            Optional[bool], Field(description="Filter by bookmarks.")
        ] = None,
        mode: Annotated[
            Optional[StrictStr], Field(description="Mode of the search.")
        ] = None,
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs
    ):  # noqa: E501
        """List teams  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_teams_with_http_info(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
        :param bookmarks: Filter by bookmarks.
        :type bookmarks: bool
        :param mode: Mode of the search.
        :type mode: str
        :param no_page: No pagination.
        :type no_page: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1ListTeamsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "offset",
            "limit",
            "sort",
            "query",
            "bookmarks",
            "mode",
            "no_page",
        ]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method list_teams" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        # process the query parameters
        _query_params = []
        if _params.get("offset") is not None:  # noqa: E501
            _query_params.append(("offset", _params["offset"]))
        if _params.get("limit") is not None:  # noqa: E501
            _query_params.append(("limit", _params["limit"]))
        if _params.get("sort") is not None:  # noqa: E501
            _query_params.append(("sort", _params["sort"]))
        if _params.get("query") is not None:  # noqa: E501
            _query_params.append(("query", _params["query"]))
        if _params.get("bookmarks") is not None:  # noqa: E501
            _query_params.append(("bookmarks", _params["bookmarks"]))
        if _params.get("mode") is not None:  # noqa: E501
            _query_params.append(("mode", _params["mode"]))
        if _params.get("no_page") is not None:  # noqa: E501
            _query_params.append(("no_page", _params["no_page"]))

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1ListTeamsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams",
            "GET",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def patch_team(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team_name: Annotated[StrictStr, Field(..., description="Name")],
        body: Annotated[V1Team, Field(..., description="Team body")],
        **kwargs
    ) -> V1Team:  # noqa: E501
        """Patch team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_team(owner, team_name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team_name: Name (required)
        :type team_name: str
        :param body: Team body (required)
        :type body: V1Team
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1Team
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_team_with_http_info(
            owner, team_name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def patch_team_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team_name: Annotated[StrictStr, Field(..., description="Name")],
        body: Annotated[V1Team, Field(..., description="Team body")],
        **kwargs
    ):  # noqa: E501
        """Patch team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_team_with_http_info(owner, team_name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team_name: Name (required)
        :type team_name: str
        :param body: Team body (required)
        :type body: V1Team
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1Team, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "team_name", "body"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method patch_team" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team_name"]:
            _path_params["team.name"] = _params["team_name"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None
        if _params["body"]:
            _body_params = _params["body"]

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["application/json"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1Team",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team.name}",
            "PATCH",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def patch_team_member(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team")],
        member_user: Annotated[StrictStr, Field(..., description="User")],
        body: Annotated[V1TeamMember, Field(..., description="Team body")],
        **kwargs
    ) -> V1TeamMember:  # noqa: E501
        """Patch team member  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_team_member(owner, team, member_user, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team (required)
        :type team: str
        :param member_user: User (required)
        :type member_user: str
        :param body: Team body (required)
        :type body: V1TeamMember
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1TeamMember
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_team_member_with_http_info(
            owner, team, member_user, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def patch_team_member_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team")],
        member_user: Annotated[StrictStr, Field(..., description="User")],
        body: Annotated[V1TeamMember, Field(..., description="Team body")],
        **kwargs
    ):  # noqa: E501
        """Patch team member  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_team_member_with_http_info(owner, team, member_user, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team (required)
        :type team: str
        :param member_user: User (required)
        :type member_user: str
        :param body: Team body (required)
        :type body: V1TeamMember
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1TeamMember, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "team", "member_user", "body"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method patch_team_member" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team"]:
            _path_params["team"] = _params["team"]
        if _params["member_user"]:
            _path_params["member.user"] = _params["member_user"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None
        if _params["body"]:
            _body_params = _params["body"]

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["application/json"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1TeamMember",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team}/members/{member.user}",
            "PATCH",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def update_team(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team_name: Annotated[StrictStr, Field(..., description="Name")],
        body: Annotated[V1Team, Field(..., description="Team body")],
        **kwargs
    ) -> V1Team:  # noqa: E501
        """Update team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_team(owner, team_name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team_name: Name (required)
        :type team_name: str
        :param body: Team body (required)
        :type body: V1Team
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1Team
        """
        kwargs["_return_http_data_only"] = True
        return self.update_team_with_http_info(
            owner, team_name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def update_team_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team_name: Annotated[StrictStr, Field(..., description="Name")],
        body: Annotated[V1Team, Field(..., description="Team body")],
        **kwargs
    ):  # noqa: E501
        """Update team  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_team_with_http_info(owner, team_name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team_name: Name (required)
        :type team_name: str
        :param body: Team body (required)
        :type body: V1Team
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1Team, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "team_name", "body"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method update_team" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team_name"]:
            _path_params["team.name"] = _params["team_name"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None
        if _params["body"]:
            _body_params = _params["body"]

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["application/json"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1Team",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team.name}",
            "PUT",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def update_team_member(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team")],
        member_user: Annotated[StrictStr, Field(..., description="User")],
        body: Annotated[V1TeamMember, Field(..., description="Team body")],
        **kwargs
    ) -> V1TeamMember:  # noqa: E501
        """Update team member  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_team_member(owner, team, member_user, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team (required)
        :type team: str
        :param member_user: User (required)
        :type member_user: str
        :param body: Team body (required)
        :type body: V1TeamMember
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: V1TeamMember
        """
        kwargs["_return_http_data_only"] = True
        return self.update_team_member_with_http_info(
            owner, team, member_user, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def update_team_member_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        team: Annotated[StrictStr, Field(..., description="Team")],
        member_user: Annotated[StrictStr, Field(..., description="User")],
        body: Annotated[V1TeamMember, Field(..., description="Team body")],
        **kwargs
    ):  # noqa: E501
        """Update team member  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_team_member_with_http_info(owner, team, member_user, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param team: Team (required)
        :type team: str
        :param member_user: User (required)
        :type member_user: str
        :param body: Team body (required)
        :type body: V1TeamMember
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(V1TeamMember, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "team", "member_user", "body"]
        _all_params.extend(
            [
                "async_req",
                "_return_http_data_only",
                "_preload_content",
                "_request_timeout",
                "_request_auth",
                "_content_type",
                "_headers",
            ]
        )

        # validate the arguments
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method update_team_member" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["team"]:
            _path_params["team"] = _params["team"]
        if _params["member_user"]:
            _path_params["member.user"] = _params["member_user"]

        # process the query parameters
        _query_params = []

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}

        # process the body parameter
        _body_params = None
        if _params["body"]:
            _body_params = _params["body"]

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["application/json"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {
            "200": "V1TeamMember",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/teams/{team}/members/{member.user}",
            "PUT",
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),  # noqa: E501
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )
