from typing import Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictStr, validate_arguments

from polyaxon._sdk.base_api import BaseApi
from polyaxon.exceptions import ApiTypeError


class ArtifactsStoresV1Api(BaseApi):
    @validate_arguments
    def upload_artifact(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Unique integer identifier of the entity")
        ],
        uploadfile: Annotated[StrictStr, Field(..., description="The file to upload.")],
        path: Annotated[
            Optional[StrictStr], Field(description="File path query params.")
        ] = None,
        overwrite: Annotated[
            Optional[bool], Field(description="File path query params.")
        ] = None,
        **kwargs
    ) -> None:
        """Upload artifact to a store

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_artifact(owner, uuid, uploadfile, path, overwrite, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param uploadfile: The file to upload. (required)
        :type uploadfile: str
        :param path: File path query params.
        :type path: str
        :param overwrite: File path query params.
        :type overwrite: bool
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
        return self.upload_artifact_with_http_info(
            owner, uuid, uploadfile, path, overwrite, **kwargs
        )

    @validate_arguments
    def upload_artifact_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        uuid: Annotated[
            StrictStr, Field(..., description="Unique integer identifier of the entity")
        ],
        uploadfile: Annotated[StrictStr, Field(..., description="The file to upload.")],
        path: Annotated[
            Optional[StrictStr], Field(description="File path query params.")
        ] = None,
        overwrite: Annotated[
            Optional[bool], Field(description="File path query params.")
        ] = None,
        **kwargs
    ):
        """Upload artifact to a store

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_artifact_with_http_info(owner, uuid, uploadfile, path, overwrite, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param uploadfile: The file to upload. (required)
        :type uploadfile: str
        :param path: File path query params.
        :type path: str
        :param overwrite: File path query params.
        :type overwrite: bool
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

        _all_params = ["owner", "uuid", "uploadfile", "path", "overwrite"]
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
                    " to method upload_artifact" % _key
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
        if _params.get("path") is not None:
            _query_params.append(("path", _params["path"]))
        if _params.get("overwrite") is not None:
            _query_params.append(("overwrite", _params["overwrite"]))

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))

        # process the form parameters
        _form_params = []
        _files = {}
        if _params["uploadfile"]:
            _files["uploadfile"] = _params["uploadfile"]

        # process the body parameter
        _body_params = None

        # set the HTTP header `Accept`
        _header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["multipart/form-data"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/catalogs/{owner}/artifacts/{uuid}/upload",
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
