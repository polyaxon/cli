from typing import Optional

from clipped.compact.pydantic import StrictInt, StrictStr, validate_call
from polyaxon._sdk.base_api import BaseApi
from polyaxon._sdk.schemas.v1_create_pty_request import V1CreatePtyRequest
from polyaxon._sdk.schemas.v1_exec_bg_list import V1ExecBgList
from polyaxon._sdk.schemas.v1_exec_bg_logs import V1ExecBgLogs
from polyaxon._sdk.schemas.v1_exec_bg_request import V1ExecBgRequest
from polyaxon._sdk.schemas.v1_exec_bg_start import V1ExecBgStart
from polyaxon._sdk.schemas.v1_exec_bg_status import V1ExecBgStatus
from polyaxon._sdk.schemas.v1_exec_request import V1ExecRequest
from polyaxon._sdk.schemas.v1_exec_result import V1ExecResult
from polyaxon._sdk.schemas.v1_fs_list_result import V1FsListResult
from polyaxon._sdk.schemas.v1_fs_mkdir_request import V1FsMkdirRequest
from polyaxon._sdk.schemas.v1_fs_path_result import V1FsPathResult
from polyaxon._sdk.schemas.v1_fs_stat_result import V1FsStatResult
from polyaxon._sdk.schemas.v1_ping_response import V1PingResponse
from polyaxon._sdk.schemas.v1_pty import V1Pty
from polyaxon._sdk.schemas.v1_pty_list import V1PtyList
from polyaxon._sdk.schemas.v1_resize_pty_request import V1ResizePtyRequest
from polyaxon._sdk.schemas.v1_signal_request import V1SignalRequest
from polyaxon.exceptions import ApiTypeError


class SandboxV1Api(BaseApi):
    @validate_call
    def call_exec(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1ExecRequest,
        **kwargs,
    ) -> V1ExecResult:  # noqa: E501
        """call_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.call_exec(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1ExecRequest
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
        :rtype: V1ExecResult
        """
        kwargs["_return_http_data_only"] = True
        return self.call_exec_with_http_info(
            namespace, owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def call_exec_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1ExecRequest,
        **kwargs,
    ):  # noqa: E501
        """call_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.call_exec_with_http_info(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1ExecRequest
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
        :rtype: tuple(V1ExecResult, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "body"]
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
                    "Got an unexpected keyword argument '%s' to method call_exec" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "200": "V1ExecResult",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec",
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
    def create_pty(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1CreatePtyRequest,
        **kwargs,
    ) -> V1Pty:  # noqa: E501
        """create_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_pty(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1CreatePtyRequest
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
        :rtype: V1Pty
        """
        kwargs["_return_http_data_only"] = True
        return self.create_pty_with_http_info(
            namespace, owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def create_pty_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1CreatePtyRequest,
        **kwargs,
    ):  # noqa: E501
        """create_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_pty_with_http_info(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1CreatePtyRequest
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
        :rtype: tuple(V1Pty, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "body"]
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
                    " to method create_pty" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "200": "V1Pty",
            "201": "V1Pty",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/pty",
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
    def delete_bg_exec(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ) -> None:  # noqa: E501
        """delete_bg_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_bg_exec(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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
        return self.delete_bg_exec_with_http_info(
            namespace, owner, project, uuid, id, **kwargs
        )  # noqa: E501

    @validate_call
    def delete_bg_exec_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ):  # noqa: E501
        """delete_bg_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_bg_exec_with_http_info(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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

        _all_params = ["namespace", "owner", "project", "uuid", "id"]
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
                    " to method delete_bg_exec" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec/bg/{id}",
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
    def delete_pty(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ) -> None:  # noqa: E501
        """delete_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_pty(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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
        return self.delete_pty_with_http_info(
            namespace, owner, project, uuid, id, **kwargs
        )  # noqa: E501

    @validate_call
    def delete_pty_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ):  # noqa: E501
        """delete_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_pty_with_http_info(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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

        _all_params = ["namespace", "owner", "project", "uuid", "id"]
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
                    " to method delete_pty" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/pty/{id}",
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
    def exec_bg(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1ExecBgRequest,
        **kwargs,
    ) -> V1ExecBgStart:  # noqa: E501
        """exec_bg  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.exec_bg(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1ExecBgRequest
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
        :rtype: V1ExecBgStart
        """
        kwargs["_return_http_data_only"] = True
        return self.exec_bg_with_http_info(
            namespace, owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def exec_bg_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1ExecBgRequest,
        **kwargs,
    ):  # noqa: E501
        """exec_bg  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.exec_bg_with_http_info(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1ExecBgRequest
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
        :rtype: tuple(V1ExecBgStart, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "body"]
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
                    "Got an unexpected keyword argument '%s' to method exec_bg" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "200": "V1ExecBgStart",
            "202": "V1ExecBgStart",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec/bg",
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
    def fs_ls(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        path: Optional[StrictStr] = None,
        recursive: Optional[bool] = None,
        max_entries: Optional[StrictInt] = None,
        **kwargs,
    ) -> V1FsListResult:  # noqa: E501
        """fs_ls  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_ls(namespace, owner, project, uuid, path, recursive, max_entries, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param path:
        :type path: str
        :param recursive:
        :type recursive: bool
        :param max_entries:
        :type max_entries: int
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
        :rtype: V1FsListResult
        """
        kwargs["_return_http_data_only"] = True
        return self.fs_ls_with_http_info(
            namespace, owner, project, uuid, path, recursive, max_entries, **kwargs
        )  # noqa: E501

    @validate_call
    def fs_ls_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        path: Optional[StrictStr] = None,
        recursive: Optional[bool] = None,
        max_entries: Optional[StrictInt] = None,
        **kwargs,
    ):  # noqa: E501
        """fs_ls  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_ls_with_http_info(namespace, owner, project, uuid, path, recursive, max_entries, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param path:
        :type path: str
        :param recursive:
        :type recursive: bool
        :param max_entries:
        :type max_entries: int
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
        :rtype: tuple(V1FsListResult, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "path",
            "recursive",
            "max_entries",
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
                    "Got an unexpected keyword argument '%s' to method fs_ls" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("path") is not None:  # noqa: E501
            _query_params.append(("path", _params["path"]))

        if _params.get("recursive") is not None:  # noqa: E501
            _query_params.append(("recursive", _params["recursive"]))

        if _params.get("max_entries") is not None:  # noqa: E501
            _query_params.append(("max_entries", _params["max_entries"]))

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
            "200": "V1FsListResult",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/fs/ls",
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
    def fs_mkdir(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1FsMkdirRequest,
        **kwargs,
    ) -> V1FsPathResult:  # noqa: E501
        """fs_mkdir  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_mkdir(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1FsMkdirRequest
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
        :rtype: V1FsPathResult
        """
        kwargs["_return_http_data_only"] = True
        return self.fs_mkdir_with_http_info(
            namespace, owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_call
    def fs_mkdir_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        body: V1FsMkdirRequest,
        **kwargs,
    ):  # noqa: E501
        """fs_mkdir  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_mkdir_with_http_info(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param body: (required)
        :type body: V1FsMkdirRequest
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
        :rtype: tuple(V1FsPathResult, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "body"]
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
                    "Got an unexpected keyword argument '%s' to method fs_mkdir" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "200": "V1FsPathResult",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/fs/mkdir",
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
    def fs_rm(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        path: Optional[StrictStr] = None,
        recursive: Optional[bool] = None,
        **kwargs,
    ) -> V1FsPathResult:  # noqa: E501
        """fs_rm  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_rm(namespace, owner, project, uuid, path, recursive, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param path:
        :type path: str
        :param recursive:
        :type recursive: bool
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
        :rtype: V1FsPathResult
        """
        kwargs["_return_http_data_only"] = True
        return self.fs_rm_with_http_info(
            namespace, owner, project, uuid, path, recursive, **kwargs
        )  # noqa: E501

    @validate_call
    def fs_rm_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        path: Optional[StrictStr] = None,
        recursive: Optional[bool] = None,
        **kwargs,
    ):  # noqa: E501
        """fs_rm  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_rm_with_http_info(namespace, owner, project, uuid, path, recursive, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param path:
        :type path: str
        :param recursive:
        :type recursive: bool
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
        :rtype: tuple(V1FsPathResult, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "path", "recursive"]
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
                    "Got an unexpected keyword argument '%s' to method fs_rm" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("path") is not None:  # noqa: E501
            _query_params.append(("path", _params["path"]))

        if _params.get("recursive") is not None:  # noqa: E501
            _query_params.append(("recursive", _params["recursive"]))

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
            "200": "V1FsPathResult",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/fs/rm",
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
    def fs_stat(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        path: Optional[StrictStr] = None,
        **kwargs,
    ) -> V1FsStatResult:  # noqa: E501
        """fs_stat  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_stat(namespace, owner, project, uuid, path, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param path:
        :type path: str
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
        :rtype: V1FsStatResult
        """
        kwargs["_return_http_data_only"] = True
        return self.fs_stat_with_http_info(
            namespace, owner, project, uuid, path, **kwargs
        )  # noqa: E501

    @validate_call
    def fs_stat_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        path: Optional[StrictStr] = None,
        **kwargs,
    ):  # noqa: E501
        """fs_stat  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.fs_stat_with_http_info(namespace, owner, project, uuid, path, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param path:
        :type path: str
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
        :rtype: tuple(V1FsStatResult, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "path"]
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
                    "Got an unexpected keyword argument '%s' to method fs_stat" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("path") is not None:  # noqa: E501
            _query_params.append(("path", _params["path"]))

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
            "200": "V1FsStatResult",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/fs/stat",
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
    def get_bg_exec(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ) -> V1ExecBgStatus:  # noqa: E501
        """get_bg_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_bg_exec(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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
        :rtype: V1ExecBgStatus
        """
        kwargs["_return_http_data_only"] = True
        return self.get_bg_exec_with_http_info(
            namespace, owner, project, uuid, id, **kwargs
        )  # noqa: E501

    @validate_call
    def get_bg_exec_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ):  # noqa: E501
        """get_bg_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_bg_exec_with_http_info(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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
        :rtype: tuple(V1ExecBgStatus, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "id"]
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
                    " to method get_bg_exec" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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
            "200": "V1ExecBgStatus",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec/bg/{id}",
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
    def get_bg_exec_logs(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        stream: Optional[StrictStr] = None,
        offset: Optional[StrictInt] = None,
        max_bytes: Optional[StrictInt] = None,
        **kwargs,
    ) -> V1ExecBgLogs:  # noqa: E501
        """get_bg_exec_logs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_bg_exec_logs(namespace, owner, project, uuid, id, stream, offset, max_bytes, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param stream:
        :type stream: str
        :param offset:
        :type offset: int
        :param max_bytes:
        :type max_bytes: int
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
        :rtype: V1ExecBgLogs
        """
        kwargs["_return_http_data_only"] = True
        return self.get_bg_exec_logs_with_http_info(
            namespace, owner, project, uuid, id, stream, offset, max_bytes, **kwargs
        )  # noqa: E501

    @validate_call
    def get_bg_exec_logs_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        stream: Optional[StrictStr] = None,
        offset: Optional[StrictInt] = None,
        max_bytes: Optional[StrictInt] = None,
        **kwargs,
    ):  # noqa: E501
        """get_bg_exec_logs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_bg_exec_logs_with_http_info(namespace, owner, project, uuid, id, stream, offset, max_bytes, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param stream:
        :type stream: str
        :param offset:
        :type offset: int
        :param max_bytes:
        :type max_bytes: int
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
        :rtype: tuple(V1ExecBgLogs, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "id",
            "stream",
            "offset",
            "max_bytes",
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
                    " to method get_bg_exec_logs" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

        # process the query parameters
        _query_params = []
        if _params.get("stream") is not None:  # noqa: E501
            _query_params.append(("stream", _params["stream"]))

        if _params.get("offset") is not None:  # noqa: E501
            _query_params.append(("offset", _params["offset"]))

        if _params.get("max_bytes") is not None:  # noqa: E501
            _query_params.append(("max_bytes", _params["max_bytes"]))

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
            "200": "V1ExecBgLogs",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec/bg/{id}/logs",
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
    def get_pty(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ) -> V1Pty:  # noqa: E501
        """get_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_pty(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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
        :rtype: V1Pty
        """
        kwargs["_return_http_data_only"] = True
        return self.get_pty_with_http_info(
            namespace, owner, project, uuid, id, **kwargs
        )  # noqa: E501

    @validate_call
    def get_pty_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        **kwargs,
    ):  # noqa: E501
        """get_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_pty_with_http_info(namespace, owner, project, uuid, id, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
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
        :rtype: tuple(V1Pty, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "id"]
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
                    "Got an unexpected keyword argument '%s' to method get_pty" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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
            "200": "V1Pty",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/pty/{id}",
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
    def list_bg_execs(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        tag: Optional[StrictStr] = None,
        **kwargs,
    ) -> V1ExecBgList:  # noqa: E501
        """list_bg_execs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_bg_execs(namespace, owner, project, uuid, tag, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param tag:
        :type tag: str
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
        :rtype: V1ExecBgList
        """
        kwargs["_return_http_data_only"] = True
        return self.list_bg_execs_with_http_info(
            namespace, owner, project, uuid, tag, **kwargs
        )  # noqa: E501

    @validate_call
    def list_bg_execs_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        tag: Optional[StrictStr] = None,
        **kwargs,
    ):  # noqa: E501
        """list_bg_execs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_bg_execs_with_http_info(namespace, owner, project, uuid, tag, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param tag:
        :type tag: str
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
        :rtype: tuple(V1ExecBgList, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "tag"]
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
                    " to method list_bg_execs" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("tag") is not None:  # noqa: E501
            _query_params.append(("tag", _params["tag"]))

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
            "200": "V1ExecBgList",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec/bg",
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
    def list_ptys(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        tag: Optional[StrictStr] = None,
        **kwargs,
    ) -> V1PtyList:  # noqa: E501
        """list_ptys  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_ptys(namespace, owner, project, uuid, tag, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param tag:
        :type tag: str
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
        :rtype: V1PtyList
        """
        kwargs["_return_http_data_only"] = True
        return self.list_ptys_with_http_info(
            namespace, owner, project, uuid, tag, **kwargs
        )  # noqa: E501

    @validate_call
    def list_ptys_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        tag: Optional[StrictStr] = None,
        **kwargs,
    ):  # noqa: E501
        """list_ptys  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_ptys_with_http_info(namespace, owner, project, uuid, tag, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param tag:
        :type tag: str
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
        :rtype: tuple(V1PtyList, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "tag"]
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
                    "Got an unexpected keyword argument '%s' to method list_ptys" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        # process the query parameters
        _query_params = []
        if _params.get("tag") is not None:  # noqa: E501
            _query_params.append(("tag", _params["tag"]))

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
            "200": "V1PtyList",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/pty",
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
    def ping(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        **kwargs,
    ) -> V1PingResponse:  # noqa: E501
        """ping  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.ping(namespace, owner, project, uuid, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
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
        :rtype: V1PingResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.ping_with_http_info(namespace, owner, project, uuid, **kwargs)  # noqa: E501

    @validate_call
    def ping_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        **kwargs,
    ):  # noqa: E501
        """ping  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.ping_with_http_info(namespace, owner, project, uuid, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
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
        :rtype: tuple(V1PingResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid"]
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
                    "Got an unexpected keyword argument '%s' to method ping" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "200": "V1PingResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/ping",
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
    def resize_pty(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        body: V1ResizePtyRequest,
        **kwargs,
    ) -> None:  # noqa: E501
        """resize_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.resize_pty(namespace, owner, project, uuid, id, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param body: (required)
        :type body: V1ResizePtyRequest
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
        return self.resize_pty_with_http_info(
            namespace, owner, project, uuid, id, body, **kwargs
        )  # noqa: E501

    @validate_call
    def resize_pty_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        body: V1ResizePtyRequest,
        **kwargs,
    ):  # noqa: E501
        """resize_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.resize_pty_with_http_info(namespace, owner, project, uuid, id, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param body: (required)
        :type body: V1ResizePtyRequest
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

        _all_params = ["namespace", "owner", "project", "uuid", "id", "body"]
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
                    " to method resize_pty" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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

        _response_types_map = {}

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/pty/{id}/resize",
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
    def signal_bg_exec(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        body: V1SignalRequest,
        **kwargs,
    ) -> None:  # noqa: E501
        """signal_bg_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.signal_bg_exec(namespace, owner, project, uuid, id, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param body: (required)
        :type body: V1SignalRequest
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
        return self.signal_bg_exec_with_http_info(
            namespace, owner, project, uuid, id, body, **kwargs
        )  # noqa: E501

    @validate_call
    def signal_bg_exec_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        body: V1SignalRequest,
        **kwargs,
    ):  # noqa: E501
        """signal_bg_exec  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.signal_bg_exec_with_http_info(namespace, owner, project, uuid, id, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param body: (required)
        :type body: V1SignalRequest
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

        _all_params = ["namespace", "owner", "project", "uuid", "id", "body"]
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
                    " to method signal_bg_exec" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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

        _response_types_map = {}

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/exec/bg/{id}/signal",
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
    def signal_pty(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        body: V1SignalRequest,
        **kwargs,
    ) -> None:  # noqa: E501
        """signal_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.signal_pty(namespace, owner, project, uuid, id, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param body: (required)
        :type body: V1SignalRequest
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
        return self.signal_pty_with_http_info(
            namespace, owner, project, uuid, id, body, **kwargs
        )  # noqa: E501

    @validate_call
    def signal_pty_with_http_info(
        self,
        namespace: StrictStr,
        owner: StrictStr,
        project: StrictStr,
        uuid: StrictStr,
        id: StrictStr,
        body: V1SignalRequest,
        **kwargs,
    ):  # noqa: E501
        """signal_pty  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.signal_pty_with_http_info(namespace, owner, project, uuid, id, body, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: (required)
        :type owner: str
        :param project: (required)
        :type project: str
        :param uuid: (required)
        :type uuid: str
        :param id: (required)
        :type id: str
        :param body: (required)
        :type body: V1SignalRequest
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

        _all_params = ["namespace", "owner", "project", "uuid", "id", "body"]
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
                    " to method signal_pty" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["namespace"]:
            _path_params["namespace"] = _params["namespace"]

        if _params["owner"]:
            _path_params["owner"] = _params["owner"]

        if _params["project"]:
            _path_params["project"] = _params["project"]

        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]

        if _params["id"]:
            _path_params["id"] = _params["id"]

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

        _response_types_map = {}

        return self.api_client.call_api(
            "/sandbox/v1/{namespace}/{owner}/{project}/runs/{uuid}/pty/{id}/signal",
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
