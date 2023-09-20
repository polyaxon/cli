from typing import Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictInt, StrictStr, validate_arguments

from polyaxon._sdk.base_api import BaseApi
from polyaxon._sdk.schemas.v1_list_presets_response import V1ListPresetsResponse
from polyaxon._sdk.schemas.v1_preset import V1Preset
from polyaxon.exceptions import ApiTypeError


class PresetsV1Api(BaseApi):
    @validate_arguments
    def create_preset(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        body: Annotated[V1Preset, Field(..., description="Preset body")],
        **kwargs
    ) -> V1Preset:
        """Create scheduling presets

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_preset(owner, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param body: Preset body (required)
        :type body: V1Preset
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
        :rtype: V1Preset
        """
        kwargs["_return_http_data_only"] = True
        return self.create_preset_with_http_info(owner, body, **kwargs)

    @validate_arguments
    def create_preset_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        body: Annotated[V1Preset, Field(..., description="Preset body")],
        **kwargs
    ):  # noqa: E501
        """Create scheduling presets  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_preset_with_http_info(owner, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param body: Preset body (required)
        :type body: V1Preset
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
        :rtype: tuple(V1Preset, status_code(int), headers(HTTPHeaderDict))
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
                    " to method create_preset" % _key
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
            "200": "V1Preset",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/presets",
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
    def delete_preset(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs
    ) -> None:  # noqa: E501
        """Delete scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_preset(owner, uuid, entity, async_req=True)
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
        return self.delete_preset_with_http_info(
            owner, uuid, entity, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_preset_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Delete scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_preset_with_http_info(owner, uuid, entity, async_req=True)
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
                    " to method delete_preset" % _key
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
            "/api/v1/orgs/{owner}/presets/{uuid}",
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
    def get_preset(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs
    ) -> V1Preset:  # noqa: E501
        """Get scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_preset(owner, uuid, entity, async_req=True)
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
        :rtype: V1Preset
        """
        kwargs["_return_http_data_only"] = True
        return self.get_preset_with_http_info(
            owner, uuid, entity, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_preset_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the sub-entity")
        ],
        entity: Annotated[
            Optional[StrictStr],
            Field(description="Entity: project name, hub name, registry name, ..."),
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_preset_with_http_info(owner, uuid, entity, async_req=True)
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
        :rtype: tuple(V1Preset, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_preset" % _key
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
            "200": "V1Preset",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/presets/{uuid}",
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
    def list_preset_names(
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
    ) -> V1ListPresetsResponse:  # noqa: E501
        """List scheduling presets names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_preset_names(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: V1ListPresetsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_preset_names_with_http_info(
            owner, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_preset_names_with_http_info(
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
        """List scheduling presets names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_preset_names_with_http_info(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: tuple(V1ListPresetsResponse, status_code(int), headers(HTTPHeaderDict))
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
                    " to method list_preset_names" % _key
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
            "200": "V1ListPresetsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/presets/names",
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
    def list_presets(
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
    ) -> V1ListPresetsResponse:  # noqa: E501
        """List scheduling presets  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_presets(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: V1ListPresetsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_presets_with_http_info(
            owner, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_presets_with_http_info(
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
        """List scheduling presets  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_presets_with_http_info(owner, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: tuple(V1ListPresetsResponse, status_code(int), headers(HTTPHeaderDict))
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
                    " to method list_presets" % _key
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
            "200": "V1ListPresetsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/presets",
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
    def patch_preset(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        preset_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Preset, Field(..., description="Preset body")],
        **kwargs
    ) -> V1Preset:  # noqa: E501
        """Patch scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_preset(owner, preset_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param preset_uuid: UUID (required)
        :type preset_uuid: str
        :param body: Preset body (required)
        :type body: V1Preset
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
        :rtype: V1Preset
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_preset_with_http_info(
            owner, preset_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def patch_preset_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        preset_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Preset, Field(..., description="Preset body")],
        **kwargs
    ):  # noqa: E501
        """Patch scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_preset_with_http_info(owner, preset_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param preset_uuid: UUID (required)
        :type preset_uuid: str
        :param body: Preset body (required)
        :type body: V1Preset
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
        :rtype: tuple(V1Preset, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "preset_uuid", "body"]
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
                    " to method patch_preset" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["preset_uuid"]:
            _path_params["preset.uuid"] = _params["preset_uuid"]

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
            "200": "V1Preset",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/presets/{preset.uuid}",
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
    def update_preset(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        preset_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Preset, Field(..., description="Preset body")],
        **kwargs
    ) -> V1Preset:  # noqa: E501
        """Update scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_preset(owner, preset_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param preset_uuid: UUID (required)
        :type preset_uuid: str
        :param body: Preset body (required)
        :type body: V1Preset
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
        :rtype: V1Preset
        """
        kwargs["_return_http_data_only"] = True
        return self.update_preset_with_http_info(
            owner, preset_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def update_preset_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        preset_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Preset, Field(..., description="Preset body")],
        **kwargs
    ):  # noqa: E501
        """Update scheduling preset  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_preset_with_http_info(owner, preset_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param preset_uuid: UUID (required)
        :type preset_uuid: str
        :param body: Preset body (required)
        :type body: V1Preset
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
        :rtype: tuple(V1Preset, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "preset_uuid", "body"]
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
                    " to method update_preset" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["preset_uuid"]:
            _path_params["preset.uuid"] = _params["preset_uuid"]

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
            "200": "V1Preset",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/orgs/{owner}/presets/{preset.uuid}",
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
