from typing import Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictStr, validate_arguments

from polyaxon._schemas.compatibility import V1Compatibility
from polyaxon._schemas.installation import V1Installation
from polyaxon._schemas.log_handler import V1LogHandler
from polyaxon._sdk.base_api import BaseApi
from polyaxon.exceptions import ApiTypeError


class VersionsV1Api(BaseApi):
    @validate_arguments
    def get_compatibility(
        self,
        uuid: Annotated[StrictStr, Field(..., description="UUid")],
        version: Annotated[StrictStr, Field(..., description="Version")],
        service: Annotated[StrictStr, Field(..., description="Service")],
        **kwargs
    ) -> V1Compatibility:
        """Get compatibility versions

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_compatibility(uuid, version, service, async_req=True)
        >>> result = thread.get()

        :param uuid: UUid (required)
        :type uuid: str
        :param version: Version (required)
        :type version: str
        :param service: Service (required)
        :type service: str
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
        :rtype: V1Compatibility
        """
        kwargs["_return_http_data_only"] = True
        return self.get_compatibility_with_http_info(uuid, version, service, **kwargs)

    @validate_arguments
    def get_compatibility_with_http_info(
        self,
        uuid: Annotated[StrictStr, Field(..., description="UUid")],
        version: Annotated[StrictStr, Field(..., description="Version")],
        service: Annotated[StrictStr, Field(..., description="Service")],
        **kwargs
    ):
        """Get compatibility versions

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_compatibility_with_http_info(uuid, version, service, async_req=True)
        >>> result = thread.get()

        :param uuid: UUid (required)
        :type uuid: str
        :param version: Version (required)
        :type version: str
        :param service: Service (required)
        :type service: str
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
        :rtype: tuple(V1Compatibility, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["uuid", "version", "service"]
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
                    " to method get_compatibility" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]
        if _params["version"]:
            _path_params["version"] = _params["version"]
        if _params["service"]:
            _path_params["service"] = _params["service"]

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
        )

        # authentication setting
        _auth_settings = ["ApiKey"]

        _response_types_map = {
            "200": "V1Compatibility",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/compatibility/{uuid}/{version}/{service}",
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
            _return_http_data_only=_params.get("_return_http_data_only"),
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            collection_formats=_collection_formats,
            _request_auth=_params.get("_request_auth"),
        )

    @validate_arguments
    def get_installation(
        self,
        auth: Annotated[Optional[bool], Field(description="auth.")] = None,
        **kwargs
    ) -> V1Installation:
        """Get installation versions

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_installation(auth, async_req=True)
        >>> result = thread.get()

        :param auth: auth.
        :type auth: bool
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
        :rtype: V1Installation
        """
        kwargs["_return_http_data_only"] = True
        return self.get_installation_with_http_info(auth, **kwargs)

    @validate_arguments
    def get_installation_with_http_info(
        self,
        auth: Annotated[Optional[bool], Field(description="auth.")] = None,
        **kwargs
    ):
        """Get installation versions

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_installation_with_http_info(auth, async_req=True)
        >>> result = thread.get()

        :param auth: auth.
        :type auth: bool
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
        :rtype: tuple(V1Installation, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["auth"]
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
                    " to method get_installation" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

        # process the query parameters
        _query_params = []
        if _params.get("auth") is not None:  # noqa: E501
            _query_params.append(("auth", _params["auth"]))

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
            "200": "V1Installation",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/installation",
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
    def get_log_handler(self, **kwargs) -> V1LogHandler:  # noqa: E501
        """Get log handler versions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_log_handler(async_req=True)
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
        :rtype: V1LogHandler
        """
        kwargs["_return_http_data_only"] = True
        return self.get_log_handler_with_http_info(**kwargs)  # noqa: E501

    @validate_arguments
    def get_log_handler_with_http_info(self, **kwargs):  # noqa: E501
        """Get log handler versions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_log_handler_with_http_info(async_req=True)
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
        :rtype: tuple(V1LogHandler, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_log_handler" % _key
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
            "200": "V1LogHandler",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/log_handler",
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
