from typing import Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictInt, StrictStr, validate_arguments

from polyaxon._sdk.base_api import BaseApi
from polyaxon._sdk.schemas.v1_list_activities_response import V1ListActivitiesResponse
from polyaxon._sdk.schemas.v1_list_token_response import V1ListTokenResponse
from polyaxon._sdk.schemas.v1_token import V1Token
from polyaxon._sdk.schemas.v1_user import V1User
from polyaxon.exceptions import ApiTypeError


class UsersV1Api(BaseApi):
    @validate_arguments
    def create_token(
        self, body: Annotated[V1Token, Field(..., description="Token body")], **kwargs
    ) -> V1Token:  # noqa: E501
        """Create token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_token(body, async_req=True)
        >>> result = thread.get()

        :param body: Token body (required)
        :type body: V1Token
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
        :rtype: V1Token
        """
        kwargs["_return_http_data_only"] = True
        return self.create_token_with_http_info(body, **kwargs)  # noqa: E501

    @validate_arguments
    def create_token_with_http_info(
        self, body: Annotated[V1Token, Field(..., description="Token body")], **kwargs
    ):  # noqa: E501
        """Create token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_token_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param body: Token body (required)
        :type body: V1Token
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
        :rtype: tuple(V1Token, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["body"]
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
                    " to method create_token" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "V1Token",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/tokens",
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
    def delete_token(
        self,
        uuid: Annotated[StrictStr, Field(..., description="UUid of the namespace")],
        **kwargs
    ) -> None:  # noqa: E501
        """Delete token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_token(uuid, async_req=True)
        >>> result = thread.get()

        :param uuid: UUid of the namespace (required)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.delete_token_with_http_info(uuid, **kwargs)  # noqa: E501

    @validate_arguments
    def delete_token_with_http_info(
        self,
        uuid: Annotated[StrictStr, Field(..., description="UUid of the namespace")],
        **kwargs
    ):  # noqa: E501
        """Delete token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_token_with_http_info(uuid, async_req=True)
        >>> result = thread.get()

        :param uuid: UUid of the namespace (required)
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
        :rtype: None
        """

        _params = locals()

        _all_params = ["uuid"]
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
                    " to method delete_token" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/users/tokens/{uuid}",
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
    def get_history(
        self,
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
        **kwargs
    ) -> V1ListActivitiesResponse:  # noqa: E501
        """User History  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_history(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        return self.get_history_with_http_info(
            offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_history_with_http_info(
        self,
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
        **kwargs
    ):  # noqa: E501
        """User History  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_history_with_http_info(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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

        _all_params = ["offset", "limit", "sort", "query", "no_page"]
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
                    " to method get_history" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "/api/v1/users/history",
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
    def get_suggestions(
        self,
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
        **kwargs
    ) -> object:  # noqa: E501
        """User suggestions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_suggestions(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        :rtype: object
        """
        kwargs["_return_http_data_only"] = True
        return self.get_suggestions_with_http_info(
            offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_suggestions_with_http_info(
        self,
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
        **kwargs
    ):  # noqa: E501
        """User suggestions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_suggestions_with_http_info(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        :rtype: tuple(object, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["offset", "limit", "sort", "query", "no_page"]
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
                    " to method get_suggestions" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "object",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/suggestions",
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
    def get_token(
        self,
        uuid: Annotated[StrictStr, Field(..., description="UUid of the namespace")],
        **kwargs
    ) -> V1Token:  # noqa: E501
        """Get token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_token(uuid, async_req=True)
        >>> result = thread.get()

        :param uuid: UUid of the namespace (required)
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
        :rtype: V1Token
        """
        kwargs["_return_http_data_only"] = True
        return self.get_token_with_http_info(uuid, **kwargs)  # noqa: E501

    @validate_arguments
    def get_token_with_http_info(
        self,
        uuid: Annotated[StrictStr, Field(..., description="UUid of the namespace")],
        **kwargs
    ):  # noqa: E501
        """Get token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_token_with_http_info(uuid, async_req=True)
        >>> result = thread.get()

        :param uuid: UUid of the namespace (required)
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
        :rtype: tuple(V1Token, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["uuid"]
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
                    " to method get_token" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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
            "200": "V1Token",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/tokens/{uuid}",
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
    def get_user(self, **kwargs) -> V1User:  # noqa: E501
        """Get current user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_user(async_req=True)
        >>> result = thread.get()

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
        :rtype: V1User
        """
        kwargs["_return_http_data_only"] = True
        return self.get_user_with_http_info(**kwargs)  # noqa: E501

    @validate_arguments
    def get_user_with_http_info(self, **kwargs):  # noqa: E501
        """Get current user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_user_with_http_info(async_req=True)
        >>> result = thread.get()

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
        :rtype: tuple(V1User, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = []
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
                    " to method get_user" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "V1User",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users",
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
    def get_workspaces(
        self,
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
        **kwargs
    ) -> object:  # noqa: E501
        """User workspaces  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_workspaces(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        :rtype: object
        """
        kwargs["_return_http_data_only"] = True
        return self.get_workspaces_with_http_info(
            offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_workspaces_with_http_info(
        self,
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
        **kwargs
    ):  # noqa: E501
        """User workspaces  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_workspaces_with_http_info(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        :rtype: tuple(object, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["offset", "limit", "sort", "query", "no_page"]
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
                    " to method get_workspaces" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "object",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/workspaces",
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
    def list_tokens(
        self,
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
        **kwargs
    ) -> V1ListTokenResponse:  # noqa: E501
        """List tokens  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_tokens(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        :rtype: V1ListTokenResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_tokens_with_http_info(
            offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_tokens_with_http_info(
        self,
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
        **kwargs
    ):  # noqa: E501
        """List tokens  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_tokens_with_http_info(offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

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
        :rtype: tuple(V1ListTokenResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["offset", "limit", "sort", "query", "no_page"]
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
                    " to method list_tokens" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "V1ListTokenResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/tokens",
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
    def patch_token(
        self,
        token_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Token, Field(..., description="Token body")],
        **kwargs
    ) -> V1Token:  # noqa: E501
        """Patch token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_token(token_uuid, body, async_req=True)
        >>> result = thread.get()

        :param token_uuid: UUID (required)
        :type token_uuid: str
        :param body: Token body (required)
        :type body: V1Token
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
        :rtype: V1Token
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_token_with_http_info(token_uuid, body, **kwargs)  # noqa: E501

    @validate_arguments
    def patch_token_with_http_info(
        self,
        token_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Token, Field(..., description="Token body")],
        **kwargs
    ):  # noqa: E501
        """Patch token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_token_with_http_info(token_uuid, body, async_req=True)
        >>> result = thread.get()

        :param token_uuid: UUID (required)
        :type token_uuid: str
        :param body: Token body (required)
        :type body: V1Token
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
        :rtype: tuple(V1Token, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["token_uuid", "body"]
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
                    " to method patch_token" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["token_uuid"]:
            _path_params["token.uuid"] = _params["token_uuid"]

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
            "200": "V1Token",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/tokens/{token.uuid}",
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
    def patch_user(self, body: V1User, **kwargs) -> V1User:  # noqa: E501
        """Patch current user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_user(body, async_req=True)
        >>> result = thread.get()

        :param body: (required)
        :type body: V1User
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
        :rtype: V1User
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_user_with_http_info(body, **kwargs)  # noqa: E501

    @validate_arguments
    def patch_user_with_http_info(self, body: V1User, **kwargs):  # noqa: E501
        """Patch current user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_user_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param body: (required)
        :type body: V1User
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
        :rtype: tuple(V1User, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["body"]
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
                    " to method patch_user" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "V1User",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users",
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
    def update_token(
        self,
        token_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Token, Field(..., description="Token body")],
        **kwargs
    ) -> V1Token:  # noqa: E501
        """Update token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_token(token_uuid, body, async_req=True)
        >>> result = thread.get()

        :param token_uuid: UUID (required)
        :type token_uuid: str
        :param body: Token body (required)
        :type body: V1Token
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
        :rtype: V1Token
        """
        kwargs["_return_http_data_only"] = True
        return self.update_token_with_http_info(
            token_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def update_token_with_http_info(
        self,
        token_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Token, Field(..., description="Token body")],
        **kwargs
    ):  # noqa: E501
        """Update token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_token_with_http_info(token_uuid, body, async_req=True)
        >>> result = thread.get()

        :param token_uuid: UUID (required)
        :type token_uuid: str
        :param body: Token body (required)
        :type body: V1Token
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
        :rtype: tuple(V1Token, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["token_uuid", "body"]
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
                    " to method update_token" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["token_uuid"]:
            _path_params["token.uuid"] = _params["token_uuid"]

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
            "200": "V1Token",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users/tokens/{token.uuid}",
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
    def update_user(self, body: V1User, **kwargs) -> V1User:  # noqa: E501
        """Update current user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_user(body, async_req=True)
        >>> result = thread.get()

        :param body: (required)
        :type body: V1User
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
        :rtype: V1User
        """
        kwargs["_return_http_data_only"] = True
        return self.update_user_with_http_info(body, **kwargs)  # noqa: E501

    @validate_arguments
    def update_user_with_http_info(self, body: V1User, **kwargs):  # noqa: E501
        """Update current user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_user_with_http_info(body, async_req=True)
        >>> result = thread.get()

        :param body: (required)
        :type body: V1User
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
        :rtype: tuple(V1User, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["body"]
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
                    " to method update_user" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

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
            "200": "V1User",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/users",
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
