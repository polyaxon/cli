from typing import Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictInt, StrictStr, validate_call

from polyaxon._sdk.base_api import BaseApi
from polyaxon._sdk.schemas.v1_automation_test_request import V1AutomationTestRequest
from polyaxon._sdk.schemas.v1_list_automation_executions_response import (
    V1ListAutomationExecutionsResponse,
)
from polyaxon._sdk.schemas.v1_list_activities_response import V1ListActivitiesResponse
from polyaxon._sdk.schemas.v1_automation import V1Automation, V1AutomationExecution
from polyaxon._sdk.schemas.v1_list_automations_response import V1ListAutomationsResponse
from polyaxon.exceptions import ApiTypeError


class AutomationsV1Api(BaseApi):
    @validate_call
    def create_automation(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        body: Annotated[V1Automation, Field(..., description="Automation")],
        **kwargs,
    ) -> V1Automation:  # noqa: E501
        """Create automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_automation(owner, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param body: Automation (required)
        :type body: V1Automation
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
        :rtype: V1Automation
        """
        kwargs["_return_http_data_only"] = True
        return self.create_automation_with_http_info(owner, body, **kwargs)  # noqa: E501

    @validate_call
    def create_automation_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        body: Annotated[V1Automation, Field(..., description="Automation")],
        **kwargs,
    ):  # noqa: E501
        """Create automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_automation_with_http_info(owner, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param body: Automation (required)
        :type body: V1Automation
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
        :rtype: tuple(V1Automation, status_code(int), headers(HTTPHeaderDict))
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
                    " to method create_automation" % _key
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
            "200": "V1Automation",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations",
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

    @validate_call
    def delete_automation(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs,
    ) -> None:  # noqa: E501
        """Delete automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_automation(owner, uuid, entity, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: Uuid identifier of the sub-entity (required)
        :type uuid: str
        :param entity: Entity: project name, hub name, registry name, ...
        :type entity: str
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
        return self.delete_automation_with_http_info(owner, uuid, entity, **kwargs)  # noqa: E501

    @validate_call
    def delete_automation_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs,
    ):  # noqa: E501
        """Delete automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_automation_with_http_info(owner, uuid, entity, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: Uuid identifier of the sub-entity (required)
        :type uuid: str
        :param entity: Entity: project name, hub name, registry name, ...
        :type entity: str
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

        _all_params = ["owner", "uuid", "entity"]
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
                    " to method delete_automation" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("entity") is not None:  # noqa: E501
            _query_params.append(("entity", _params["entity"]))

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
            "/api/v1/orgs/{owner}/automations/{uuid}",
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

    @validate_call
    def get_automation(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs,
    ) -> V1Automation:  # noqa: E501
        """Get automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_automation(owner, uuid, entity, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: Uuid identifier of the sub-entity (required)
        :type uuid: str
        :param entity: Entity: project name, hub name, registry name, ...
        :type entity: str
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
        :rtype: V1Automation
        """
        kwargs["_return_http_data_only"] = True
        return self.get_automation_with_http_info(owner, uuid, entity, **kwargs)  # noqa: E501

    @validate_call
    def get_automation_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs,
    ):  # noqa: E501
        """Get automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_automation_with_http_info(owner, uuid, entity, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: Uuid identifier of the sub-entity (required)
        :type uuid: str
        :param entity: Entity: project name, hub name, registry name, ...
        :type entity: str
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
        :rtype: tuple(V1Automation, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "uuid", "entity"]
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
                    " to method get_automation" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("entity") is not None:  # noqa: E501
            _query_params.append(("entity", _params["entity"]))

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
            "200": "V1Automation",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{uuid}",
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

    @validate_call
    def get_automation_stats(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
        entity: Annotated[
            Optional[StrictStr], Field(description="Entity name under namespace.")
        ] = None,
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
        mode: Annotated[Optional[StrictStr], Field(description="Stats Mode.")] = None,
        kind: Annotated[Optional[StrictStr], Field(description="Stats Kind.")] = None,
        aggregate: Annotated[
            Optional[StrictStr], Field(description="Stats aggregate.")
        ] = None,
        groupby: Annotated[
            Optional[StrictStr], Field(description="Stats group.")
        ] = None,
        trunc: Annotated[Optional[StrictStr], Field(description="Stats trunc.")] = None,
        start_date: Annotated[
            Optional[StrictStr], Field(description="Stats start date.")
        ] = None,
        end_date: Annotated[
            Optional[StrictStr], Field(description="Stats end date.")
        ] = None,
        boundary: Annotated[
            Optional[bool], Field(description="Stats boundary.")
        ] = None,
        **kwargs,
    ) -> object:  # noqa: E501
        """Get automation stats  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_automation_stats(owner, uuid, entity, offset, limit, sort, query, bookmarks, mode, kind, aggregate, groupby, trunc, start_date, end_date, boundary, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
        :param entity: Entity name under namespace.
        :type entity: str
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
        :param mode: Stats Mode.
        :type mode: str
        :param kind: Stats Kind.
        :type kind: str
        :param aggregate: Stats aggregate.
        :type aggregate: str
        :param groupby: Stats group.
        :type groupby: str
        :param trunc: Stats trunc.
        :type trunc: str
        :param start_date: Stats start date.
        :type start_date: str
        :param end_date: Stats end date.
        :type end_date: str
        :param boundary: Stats boundary.
        :type boundary: bool
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
        :rtype: object
        """
        kwargs["_return_http_data_only"] = True
        return self.get_automation_stats_with_http_info(
            owner,
            uuid,
            entity,
            offset,
            limit,
            sort,
            query,
            bookmarks,
            mode,
            kind,
            aggregate,
            groupby,
            trunc,
            start_date,
            end_date,
            boundary,
            **kwargs,
        )  # noqa: E501

    @validate_call
    def get_automation_stats_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
        entity: Annotated[
            Optional[StrictStr], Field(description="Entity name under namespace.")
        ] = None,
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
        mode: Annotated[Optional[StrictStr], Field(description="Stats Mode.")] = None,
        kind: Annotated[Optional[StrictStr], Field(description="Stats Kind.")] = None,
        aggregate: Annotated[
            Optional[StrictStr], Field(description="Stats aggregate.")
        ] = None,
        groupby: Annotated[
            Optional[StrictStr], Field(description="Stats group.")
        ] = None,
        trunc: Annotated[Optional[StrictStr], Field(description="Stats trunc.")] = None,
        start_date: Annotated[
            Optional[StrictStr], Field(description="Stats start date.")
        ] = None,
        end_date: Annotated[
            Optional[StrictStr], Field(description="Stats end date.")
        ] = None,
        boundary: Annotated[
            Optional[bool], Field(description="Stats boundary.")
        ] = None,
        **kwargs,
    ):  # noqa: E501
        """Get automation stats  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_automation_stats_with_http_info(owner, uuid, entity, offset, limit, sort, query, bookmarks, mode, kind, aggregate, groupby, trunc, start_date, end_date, boundary, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
        :param entity: Entity name under namespace.
        :type entity: str
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
        :param mode: Stats Mode.
        :type mode: str
        :param kind: Stats Kind.
        :type kind: str
        :param aggregate: Stats aggregate.
        :type aggregate: str
        :param groupby: Stats group.
        :type groupby: str
        :param trunc: Stats trunc.
        :type trunc: str
        :param start_date: Stats start date.
        :type start_date: str
        :param end_date: Stats end date.
        :type end_date: str
        :param boundary: Stats boundary.
        :type boundary: bool
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
        :rtype: tuple(object, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "uuid",
            "entity",
            "offset",
            "limit",
            "sort",
            "query",
            "bookmarks",
            "mode",
            "kind",
            "aggregate",
            "groupby",
            "trunc",
            "start_date",
            "end_date",
            "boundary",
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
                    " to method get_automation_stats" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("entity") is not None:  # noqa: E501
            _query_params.append(("entity", _params["entity"]))

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

        if _params.get("kind") is not None:  # noqa: E501
            _query_params.append(("kind", _params["kind"]))

        if _params.get("aggregate") is not None:  # noqa: E501
            _query_params.append(("aggregate", _params["aggregate"]))

        if _params.get("groupby") is not None:  # noqa: E501
            _query_params.append(("groupby", _params["groupby"]))

        if _params.get("trunc") is not None:  # noqa: E501
            _query_params.append(("trunc", _params["trunc"]))

        if _params.get("start_date") is not None:  # noqa: E501
            _query_params.append(("start_date", _params["start_date"]))

        if _params.get("end_date") is not None:  # noqa: E501
            _query_params.append(("end_date", _params["end_date"]))

        if _params.get("boundary") is not None:  # noqa: E501
            _query_params.append(("boundary", _params["boundary"]))

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
            "200": "object",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{uuid}/stats",
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

    @validate_call
    def list_automation_events(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
        entity: Annotated[
            Optional[StrictStr], Field(description="Entity name under namespace.")
        ] = None,
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
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs,
    ) -> V1ListActivitiesResponse:  # noqa: E501
        """List automation events (from executions' triggering_event)  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automation_events(owner, uuid, entity, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
        :param entity: Entity name under namespace.
        :type entity: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
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
        :rtype: V1ListActivitiesResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_automation_events_with_http_info(
            owner, uuid, entity, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_call
    def list_automation_events_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
        entity: Annotated[
            Optional[StrictStr], Field(description="Entity name under namespace.")
        ] = None,
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
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs,
    ):  # noqa: E501
        """List automation events (from executions' triggering_event)  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automation_events_with_http_info(owner, uuid, entity, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
        :param entity: Entity name under namespace.
        :type entity: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
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
        :rtype: tuple(V1ListActivitiesResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "uuid",
            "entity",
            "offset",
            "limit",
            "sort",
            "query",
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
                    " to method list_automation_events" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("entity") is not None:  # noqa: E501
            _query_params.append(("entity", _params["entity"]))

        if _params.get("offset") is not None:  # noqa: E501
            _query_params.append(("offset", _params["offset"]))

        if _params.get("limit") is not None:  # noqa: E501
            _query_params.append(("limit", _params["limit"]))

        if _params.get("sort") is not None:  # noqa: E501
            _query_params.append(("sort", _params["sort"]))

        if _params.get("query") is not None:  # noqa: E501
            _query_params.append(("query", _params["query"]))

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
            "200": "V1ListActivitiesResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{uuid}/events",
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

    @validate_call
    def list_automation_executions(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
        entity: Annotated[
            Optional[StrictStr], Field(description="Entity name under namespace.")
        ] = None,
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
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs,
    ) -> V1ListAutomationExecutionsResponse:  # noqa: E501
        """List automation executions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automation_executions(owner, uuid, entity, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
        :param entity: Entity name under namespace.
        :type entity: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
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
        :rtype: V1ListAutomationExecutionsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_automation_executions_with_http_info(
            owner, uuid, entity, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_call
    def list_automation_executions_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
        entity: Annotated[
            Optional[StrictStr], Field(description="Entity name under namespace.")
        ] = None,
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
        no_page: Annotated[Optional[bool], Field(description="No pagination.")] = None,
        **kwargs,
    ):  # noqa: E501
        """List automation executions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automation_executions_with_http_info(owner, uuid, entity, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
        :param entity: Entity name under namespace.
        :type entity: str
        :param offset: Pagination offset.
        :type offset: int
        :param limit: Limit size.
        :type limit: int
        :param sort: Sort to order the search.
        :type sort: str
        :param query: Query filter the search.
        :type query: str
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
        :rtype: tuple(V1ListAutomationExecutionsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "uuid",
            "entity",
            "offset",
            "limit",
            "sort",
            "query",
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
                    " to method list_automation_executions" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("entity") is not None:  # noqa: E501
            _query_params.append(("entity", _params["entity"]))

        if _params.get("offset") is not None:  # noqa: E501
            _query_params.append(("offset", _params["offset"]))

        if _params.get("limit") is not None:  # noqa: E501
            _query_params.append(("limit", _params["limit"]))

        if _params.get("sort") is not None:  # noqa: E501
            _query_params.append(("sort", _params["sort"]))

        if _params.get("query") is not None:  # noqa: E501
            _query_params.append(("query", _params["query"]))

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
            "200": "V1ListAutomationExecutionsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{uuid}/executions",
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

    @validate_call
    def list_automation_names(
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
        **kwargs,
    ) -> V1ListAutomationsResponse:  # noqa: E501
        """List automation names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automation_names(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: V1ListAutomationsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_automation_names_with_http_info(
            owner, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_call
    def list_automation_names_with_http_info(
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
        **kwargs,
    ):  # noqa: E501
        """List automation names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automation_names_with_http_info(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: tuple(V1ListAutomationsResponse, status_code(int), headers(HTTPHeaderDict))
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
                    " to method list_automation_names" % _key
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
            "200": "V1ListAutomationsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/names",
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

    @validate_call
    def list_automations(
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
        **kwargs,
    ) -> V1ListAutomationsResponse:  # noqa: E501
        """List automations  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automations(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: V1ListAutomationsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_automations_with_http_info(
            owner, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_call
    def list_automations_with_http_info(
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
        **kwargs,
    ):  # noqa: E501
        """List automations  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_automations_with_http_info(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: tuple(V1ListAutomationsResponse, status_code(int), headers(HTTPHeaderDict))
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
                    " to method list_automations" % _key
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
            "200": "V1ListAutomationsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations",
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

    @validate_call
    def patch_automation(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        automation_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Automation, Field(..., description="Automation")],
        **kwargs,
    ) -> V1Automation:  # noqa: E501
        """Patch automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_automation(owner, automation_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param automation_uuid: UUID (required)
        :type automation_uuid: str
        :param body: Automation (required)
        :type body: V1Automation
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
        :rtype: V1Automation
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_automation_with_http_info(
            owner, automation_uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def patch_automation_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        automation_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Automation, Field(..., description="Automation")],
        **kwargs,
    ):  # noqa: E501
        """Patch automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_automation_with_http_info(owner, automation_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param automation_uuid: UUID (required)
        :type automation_uuid: str
        :param body: Automation (required)
        :type body: V1Automation
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
        :rtype: tuple(V1Automation, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "automation_uuid", "body"]
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
                    " to method patch_automation" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["automation_uuid"]:
            _path_params["automation.uuid"] = _params["automation_uuid"]

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
            "200": "V1Automation",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{automation.uuid}",
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

    @validate_call
    def retry_automation_execution(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr,
            Field(
                ..., description="Entity: project name, hub name, registry name, ..."
            ),
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        **kwargs,
    ) -> V1AutomationExecution:  # noqa: E501
        """Retry automation execution  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.retry_automation_execution(owner, entity, uuid, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity: project name, hub name, registry name, ... (required)
        :type entity: str
        :param uuid: Uuid identifier of the sub-entity (required)
        :type uuid: str
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
        :rtype: V1AutomationExecution
        """
        kwargs["_return_http_data_only"] = True
        return self.retry_automation_execution_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_call
    def retry_automation_execution_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr,
            Field(
                ..., description="Entity: project name, hub name, registry name, ..."
            ),
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        **kwargs,
    ):  # noqa: E501
        """Retry automation execution  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.retry_automation_execution_with_http_info(owner, entity, uuid, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity: project name, hub name, registry name, ... (required)
        :type entity: str
        :param uuid: Uuid identifier of the sub-entity (required)
        :type uuid: str
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
        :rtype: tuple(V1AutomationExecution, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "entity", "uuid"]
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
                    " to method retry_automation_execution" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["entity"]:
            _path_params["entity"] = _params["entity"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

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
            "200": "V1AutomationExecution",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{entity}/executions/{uuid}/retry",
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

    @validate_call
    def test_automation(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        automation_uuid: Annotated[
            StrictStr, Field(..., description="Automation UUID")
        ],
        body: V1AutomationTestRequest,
        **kwargs,
    ) -> object:  # noqa: E501
        """Test automation trigger evaluation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.test_automation(owner, automation_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param automation_uuid: Automation UUID (required)
        :type automation_uuid: str
        :param body: (required)
        :type body: V1AutomationTestRequest
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
        :rtype: object
        """
        kwargs["_return_http_data_only"] = True
        return self.test_automation_with_http_info(
            owner, automation_uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def test_automation_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        automation_uuid: Annotated[
            StrictStr, Field(..., description="Automation UUID")
        ],
        body: V1AutomationTestRequest,
        **kwargs,
    ):  # noqa: E501
        """Test automation trigger evaluation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.test_automation_with_http_info(owner, automation_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param automation_uuid: Automation UUID (required)
        :type automation_uuid: str
        :param body: (required)
        :type body: V1AutomationTestRequest
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
        :rtype: tuple(object, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "automation_uuid", "body"]
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
                    " to method test_automation" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["automation_uuid"]:
            _path_params["automation_uuid"] = _params["automation_uuid"]

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
            "200": "object",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{automation_uuid}/test",
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

    @validate_call
    def update_automation(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        automation_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Automation, Field(..., description="Automation")],
        **kwargs,
    ) -> V1Automation:  # noqa: E501
        """Update automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_automation(owner, automation_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param automation_uuid: UUID (required)
        :type automation_uuid: str
        :param body: Automation (required)
        :type body: V1Automation
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
        :rtype: V1Automation
        """
        kwargs["_return_http_data_only"] = True
        return self.update_automation_with_http_info(
            owner, automation_uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def update_automation_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        automation_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Automation, Field(..., description="Automation")],
        **kwargs,
    ):  # noqa: E501
        """Update automation  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_automation_with_http_info(owner, automation_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param automation_uuid: UUID (required)
        :type automation_uuid: str
        :param body: Automation (required)
        :type body: V1Automation
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
        :rtype: tuple(V1Automation, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "automation_uuid", "body"]
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
                    " to method update_automation" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["automation_uuid"]:
            _path_params["automation.uuid"] = _params["automation_uuid"]

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
            "200": "V1Automation",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/automations/{automation.uuid}",
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
