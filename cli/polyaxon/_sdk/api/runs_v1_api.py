from datetime import datetime
from typing import Any, Dict, Optional
from typing_extensions import Annotated

from clipped.compact.pydantic import Field, StrictInt, StrictStr, validate_arguments

from polyaxon._schemas.lifecycle import V1Status
from polyaxon._sdk.base_api import BaseApi
from polyaxon._sdk.schemas import V1RunEdgesGraph
from polyaxon._sdk.schemas.v1_artifact_tree import V1ArtifactTree
from polyaxon._sdk.schemas.v1_auth import V1Auth
from polyaxon._sdk.schemas.v1_entities_tags import V1EntitiesTags
from polyaxon._sdk.schemas.v1_entities_transfer import V1EntitiesTransfer
from polyaxon._sdk.schemas.v1_entity_notification_body import V1EntityNotificationBody
from polyaxon._sdk.schemas.v1_entity_status_body_request import (
    V1EntityStatusBodyRequest,
)
from polyaxon._sdk.schemas.v1_events_response import (
    V1EventsResponse,
    V1MultiEventsResponse,
)
from polyaxon._sdk.schemas.v1_list_bookmarks_response import V1ListBookmarksResponse
from polyaxon._sdk.schemas.v1_list_run_artifacts_response import (
    V1ListRunArtifactsResponse,
)
from polyaxon._sdk.schemas.v1_list_run_connections_response import (
    V1ListRunConnectionsResponse,
)
from polyaxon._sdk.schemas.v1_list_run_edges_response import V1ListRunEdgesResponse
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_operation_body import V1OperationBody
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_run_settings import V1RunSettings
from polyaxon._sdk.schemas.v1_uuids import V1Uuids
from polyaxon.exceptions import ApiTypeError
from traceml.artifacts import V1RunArtifact, V1RunArtifacts
from traceml.logging import V1Logs


class RunsV1Api(BaseApi):
    @validate_arguments
    def approve_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Approve run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.approve_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.approve_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def approve_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Approve run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.approve_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method approve_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/approve",
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
    def approve_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Approve runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.approve_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.approve_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def approve_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Approve runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.approve_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method approve_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/approve",
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
    def archive_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Archive run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.archive_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.archive_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def archive_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Archive run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.archive_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method archive_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/archive",
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
    def archive_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Archive runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.archive_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.archive_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def archive_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Archive runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.archive_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method archive_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/archive",
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
    def bookmark_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Bookmark run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.bookmark_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.bookmark_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def bookmark_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Bookmark run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.bookmark_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method bookmark_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/bookmark",
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
    def bookmark_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Bookmark runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.bookmark_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.bookmark_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def bookmark_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Bookmark runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.bookmark_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method bookmark_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/bookmark",
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
    def collect_run_logs(
        self,
        namespace: StrictStr,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        kind: Annotated[str, Field(..., description="Kind of the entity")],
        **kwargs
    ) -> None:  # noqa: E501
        """Internal API to collect run logs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.collect_run_logs(namespace, owner, project, uuid, kind, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param kind: Kind of the entity (required)
        :type kind: str
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
        return self.collect_run_logs_with_http_info(
            namespace, owner, project, uuid, kind, **kwargs
        )  # noqa: E501

    @validate_arguments
    def collect_run_logs_with_http_info(
        self,
        namespace: StrictStr,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        kind: Annotated[str, Field(..., description="Kind of the entity")],
        **kwargs
    ):  # noqa: E501
        """Internal API to collect run logs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.collect_run_logs_with_http_info(namespace, owner, project, uuid, kind, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param kind: Kind of the entity (required)
        :type kind: str
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

        _all_params = ["namespace", "owner", "project", "uuid", "kind"]
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
                    " to method collect_run_logs" % _key
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
        if _params["kind"]:
            _path_params["kind"] = _params["kind"]

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
            "/internal/v1/{namespace}/{owner}/{project}/runs/{uuid}/{kind}/logs",
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
    def copy_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Restart run with copy  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.copy_run(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.copy_run_with_http_info(
            owner, project, run_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def copy_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Restart run with copy  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.copy_run_with_http_info(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "run_uuid", "body"]
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
                    " to method copy_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["run_uuid"]:
            _path_params["run.uuid"] = _params["run_uuid"]

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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{run.uuid}/copy",
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
    def create_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        body: Annotated[V1OperationBody, Field(..., description="operation object")],
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Create new run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_run(owner, project, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param body: operation object (required)
        :type body: V1OperationBody
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.create_run_with_http_info(
            owner, project, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def create_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        body: Annotated[V1OperationBody, Field(..., description="operation object")],
        **kwargs
    ):  # noqa: E501
        """Create new run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_run_with_http_info(owner, project, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param body: operation object (required)
        :type body: V1OperationBody
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "body"]
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
                    " to method create_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs",
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
    def create_run_artifacts_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        body: Annotated[V1RunArtifacts, Field(..., description="Run Artifacts")],
        **kwargs
    ) -> None:  # noqa: E501
        """Create bulk run artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_run_artifacts_lineage(owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param body: Run Artifacts (required)
        :type body: V1RunArtifacts
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
        return self.create_run_artifacts_lineage_with_http_info(
            owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def create_run_artifacts_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        body: Annotated[V1RunArtifacts, Field(..., description="Run Artifacts")],
        **kwargs
    ):  # noqa: E501
        """Create bulk run artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_run_artifacts_lineage_with_http_info(owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param body: Run Artifacts (required)
        :type body: V1RunArtifacts
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

        _all_params = ["owner", "project", "uuid", "body"]
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
                    " to method create_run_artifacts_lineage" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{uuid}/lineage/artifacts",
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
    def create_run_status(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        body: V1EntityStatusBodyRequest,
        **kwargs
    ) -> V1Status:  # noqa: E501
        """Create new run status  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_run_status(owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param body: (required)
        :type body: V1EntityStatusBodyRequest
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
        :rtype: V1Status
        """
        kwargs["_return_http_data_only"] = True
        return self.create_run_status_with_http_info(
            owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def create_run_status_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        body: V1EntityStatusBodyRequest,
        **kwargs
    ):  # noqa: E501
        """Create new run status  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_run_status_with_http_info(owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param body: (required)
        :type body: V1EntityStatusBodyRequest
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
        :rtype: tuple(V1Status, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "uuid", "body"]
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
                    " to method create_run_status" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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
            "200": "V1Status",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{uuid}/statuses",
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
    def delete_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Delete run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.delete_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Delete run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method delete_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}",
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
    def delete_run_artifact(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Path query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        **kwargs
    ) -> None:  # noqa: E501
        """Delete run artifact  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_artifact(namespace, owner, project, uuid, path, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param path: Path query param.
        :type path: str
        :param connection: Connection query param.
        :type connection: str
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
        return self.delete_run_artifact_with_http_info(
            namespace, owner, project, uuid, path, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_run_artifact_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Path query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Delete run artifact  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_artifact_with_http_info(namespace, owner, project, uuid, path, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param path: Path query param.
        :type path: str
        :param connection: Connection query param.
        :type connection: str
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

        _all_params = ["namespace", "owner", "project", "uuid", "path", "connection"]
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
                    " to method delete_run_artifact" % _key
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
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/artifact",
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
    def delete_run_artifact_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        name: Annotated[StrictStr, Field(..., description="Artifact name")],
        namespace: Annotated[
            Optional[StrictStr], Field(description="namespace.")
        ] = None,
        **kwargs
    ) -> None:  # noqa: E501
        """Delete run artifact lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_artifact_lineage(owner, project, uuid, name, namespace, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param name: Artifact name (required)
        :type name: str
        :param namespace: namespace.
        :type namespace: str
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
        return self.delete_run_artifact_lineage_with_http_info(
            owner, project, uuid, name, namespace, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_run_artifact_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        name: Annotated[StrictStr, Field(..., description="Artifact name")],
        namespace: Annotated[
            Optional[StrictStr], Field(description="namespace.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Delete run artifact lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_artifact_lineage_with_http_info(owner, project, uuid, name, namespace, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param name: Artifact name (required)
        :type name: str
        :param namespace: namespace.
        :type namespace: str
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

        _all_params = ["owner", "project", "uuid", "name", "namespace"]
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
                    " to method delete_run_artifact_lineage" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]
        if _params["name"]:
            _path_params["name"] = _params["name"]

        # process the query parameters
        _query_params = []
        if _params.get("namespace") is not None:  # noqa: E501
            _query_params.append(("namespace", _params["namespace"]))

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
            "/api/v1/{owner}/{project}/runs/{uuid}/lineage/artifacts/{name}",
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
    def delete_run_artifacts(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Path query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        **kwargs
    ) -> None:  # noqa: E501
        """Delete run artifacts  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_artifacts(namespace, owner, project, uuid, path, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param path: Path query param.
        :type path: str
        :param connection: Connection query param.
        :type connection: str
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
        return self.delete_run_artifacts_with_http_info(
            namespace, owner, project, uuid, path, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_run_artifacts_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Path query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Delete run artifacts  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_run_artifacts_with_http_info(namespace, owner, project, uuid, path, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param path: Path query param.
        :type path: str
        :param connection: Connection query param.
        :type connection: str
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

        _all_params = ["namespace", "owner", "project", "uuid", "path", "connection"]
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
                    " to method delete_run_artifacts" % _key
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
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/artifacts",
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
    def delete_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Delete runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_runs(owner, project, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.delete_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def delete_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Delete runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method delete_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/delete",
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
    def get_multi_run_events(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        kind: Annotated[str, Field(..., description="The artifact kind")],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        runs: Annotated[
            Optional[StrictStr], Field(description="Runs query param.")
        ] = None,
        orient: Annotated[
            Optional[StrictStr], Field(description="Orient query param.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ) -> V1MultiEventsResponse:  # noqa: E501
        """Get multi runs events  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_multi_run_events(namespace, owner, project, kind, names, runs, orient, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param kind: The artifact kind (required)
        :type kind: str
        :param names: Names query param.
        :type names: str
        :param runs: Runs query param.
        :type runs: str
        :param orient: Orient query param.
        :type orient: str
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection query param.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        :rtype: V1MultiEventsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_multi_run_events_with_http_info(
            namespace,
            owner,
            project,
            kind,
            names,
            runs,
            orient,
            force,
            sample,
            connection,
            status,
            **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_multi_run_events_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        kind: Annotated[str, Field(..., description="The artifact kind")],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        runs: Annotated[
            Optional[StrictStr], Field(description="Runs query param.")
        ] = None,
        orient: Annotated[
            Optional[StrictStr], Field(description="Orient query param.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get multi runs events  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_multi_run_events_with_http_info(namespace, owner, project, kind, names, runs, orient, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param kind: The artifact kind (required)
        :type kind: str
        :param names: Names query param.
        :type names: str
        :param runs: Runs query param.
        :type runs: str
        :param orient: Orient query param.
        :type orient: str
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection query param.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        :rtype: tuple(V1MultiEventsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "kind",
            "names",
            "runs",
            "orient",
            "force",
            "sample",
            "connection",
            "status",
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
                    " to method get_multi_run_events" % _key
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
        if _params["kind"]:
            _path_params["kind"] = _params["kind"]

        # process the query parameters
        _query_params = []
        if _params.get("names") is not None:  # noqa: E501
            _query_params.append(("names", _params["names"]))
        if _params.get("runs") is not None:  # noqa: E501
            _query_params.append(("runs", _params["runs"]))
        if _params.get("orient") is not None:  # noqa: E501
            _query_params.append(("orient", _params["orient"]))
        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))
        if _params.get("sample") is not None:  # noqa: E501
            _query_params.append(("sample", _params["sample"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))
        if _params.get("status") is not None:  # noqa: E501
            _query_params.append(("status", _params["status"]))

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
            "200": "V1MultiEventsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/multi/events/{kind}",
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
    def get_multi_run_importance(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        body: Annotated[Dict[str, Any], Field(..., description="Params/Metrics data")],
        **kwargs
    ) -> V1MultiEventsResponse:  # noqa: E501
        """Get multi run importance  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_multi_run_importance(namespace, owner, project, body, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param body: Params/Metrics data (required)
        :type body: object
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
        :rtype: V1MultiEventsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_multi_run_importance_with_http_info(
            namespace, owner, project, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_multi_run_importance_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        body: Annotated[Dict[str, Any], Field(..., description="Params/Metrics data")],
        **kwargs
    ):  # noqa: E501
        """Get multi run importance  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_multi_run_importance_with_http_info(namespace, owner, project, body, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param body: Params/Metrics data (required)
        :type body: object
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
        :rtype: tuple(V1MultiEventsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "body"]
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
                    " to method get_multi_run_importance" % _key
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
            "200": "V1MultiEventsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/multi/importance",
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
    def get_run(
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
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Get run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run(owner, entity, uuid, async_req=True)
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_with_http_info(owner, entity, uuid, **kwargs)  # noqa: E501

    @validate_arguments
    def get_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Get run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_run" % _key
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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}",
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
    def get_run_artifact(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr,
            Field(..., description="Project where the entity will be assigned"),
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Unique integer identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Artifact filepath.")
        ] = None,
        stream: Annotated[
            Optional[bool], Field(description="Whether to stream the file.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Whether to force reload.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ) -> str:  # noqa: E501
        """Get run artifact  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifact(namespace, owner, project, uuid, path, stream, force, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the entity will be assigned (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param path: Artifact filepath.
        :type path: str
        :param stream: Whether to stream the file.
        :type stream: bool
        :param force: Whether to force reload.
        :type force: bool
        :param connection: Connection to use.
        :type connection: str
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
        :rtype: str
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_artifact_with_http_info(
            namespace, owner, project, uuid, path, stream, force, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_artifact_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr,
            Field(..., description="Project where the entity will be assigned"),
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Unique integer identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Artifact filepath.")
        ] = None,
        stream: Annotated[
            Optional[bool], Field(description="Whether to stream the file.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Whether to force reload.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run artifact  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifact_with_http_info(namespace, owner, project, uuid, path, stream, force, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the entity will be assigned (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param path: Artifact filepath.
        :type path: str
        :param stream: Whether to stream the file.
        :type stream: bool
        :param force: Whether to force reload.
        :type force: bool
        :param connection: Connection to use.
        :type connection: str
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
        :rtype: tuple(str, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "path",
            "stream",
            "force",
            "connection",
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
                    " to method get_run_artifact" % _key
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
        if _params.get("stream") is not None:  # noqa: E501
            _query_params.append(("stream", _params["stream"]))
        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
            "200": "str",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/artifact",
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
    def get_run_artifact_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        name: Annotated[StrictStr, Field(..., description="Artifact name")],
        namespace: Annotated[
            Optional[StrictStr], Field(description="namespace.")
        ] = None,
        **kwargs
    ) -> V1RunArtifact:  # noqa: E501
        """Get run artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifact_lineage(owner, project, uuid, name, namespace, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param name: Artifact name (required)
        :type name: str
        :param namespace: namespace.
        :type namespace: str
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
        :rtype: V1RunArtifact
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_artifact_lineage_with_http_info(
            owner, project, uuid, name, namespace, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_artifact_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        name: Annotated[StrictStr, Field(..., description="Artifact name")],
        namespace: Annotated[
            Optional[StrictStr], Field(description="namespace.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifact_lineage_with_http_info(owner, project, uuid, name, namespace, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param name: Artifact name (required)
        :type name: str
        :param namespace: namespace.
        :type namespace: str
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
        :rtype: tuple(V1RunArtifact, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "uuid", "name", "namespace"]
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
                    " to method get_run_artifact_lineage" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["uuid"]:
            _path_params["uuid"] = _params["uuid"]
        if _params["name"]:
            _path_params["name"] = _params["name"]

        # process the query parameters
        _query_params = []
        if _params.get("namespace") is not None:  # noqa: E501
            _query_params.append(("namespace", _params["namespace"]))

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
            "200": "V1RunArtifact",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{uuid}/lineage/artifacts/{name}",
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
    def get_run_artifacts(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr,
            Field(..., description="Project where the entity will be assigned"),
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Unique integer identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Artifact filepath.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Whether to force reload.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ) -> str:  # noqa: E501
        """Get run artifacts  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts(namespace, owner, project, uuid, path, force, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the entity will be assigned (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param path: Artifact filepath.
        :type path: str
        :param force: Whether to force reload.
        :type force: bool
        :param connection: Connection to use.
        :type connection: str
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
        :rtype: str
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_artifacts_with_http_info(
            namespace, owner, project, uuid, path, force, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_artifacts_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr,
            Field(..., description="Project where the entity will be assigned"),
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Unique integer identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Artifact filepath.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Whether to force reload.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run artifacts  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_with_http_info(namespace, owner, project, uuid, path, force, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the entity will be assigned (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param path: Artifact filepath.
        :type path: str
        :param force: Whether to force reload.
        :type force: bool
        :param connection: Connection to use.
        :type connection: str
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
        :rtype: tuple(str, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "path",
            "force",
            "connection",
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
                    " to method get_run_artifacts" % _key
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

        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))

        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
            "200": "str",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/artifacts",
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
    def get_run_artifacts_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
    ) -> V1ListRunArtifactsResponse:  # noqa: E501
        """Get run artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_lineage(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: V1ListRunArtifactsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_artifacts_lineage_with_http_info(
            owner, entity, uuid, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_artifacts_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        """Get run artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_lineage_with_http_info(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: tuple(V1ListRunArtifactsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "entity",
            "uuid",
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
                    " to method get_run_artifacts_lineage" % _key
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
            "200": "V1ListRunArtifactsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/lineage/artifacts",
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
    def get_run_artifacts_lineage_names(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
    ) -> V1ListRunArtifactsResponse:  # noqa: E501
        """Get run artifacts lineage names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_lineage_names(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: V1ListRunArtifactsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_artifacts_lineage_names_with_http_info(
            owner, entity, uuid, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_artifacts_lineage_names_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        """Get run artifacts lineage names  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_lineage_names_with_http_info(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: tuple(V1ListRunArtifactsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "entity",
            "uuid",
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
                    " to method get_run_artifacts_lineage_names" % _key
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
            "200": "V1ListRunArtifactsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/lineage/artifacts/names",
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
    def get_run_artifacts_tree(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Path query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        **kwargs
    ) -> V1ArtifactTree:  # noqa: E501
        """Get run artifacts tree  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_tree(namespace, owner, project, uuid, path, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param path: Path query param.
        :type path: str
        :param connection: Connection query param.
        :type connection: str
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
        :rtype: V1ArtifactTree
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_artifacts_tree_with_http_info(
            namespace, owner, project, uuid, path, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_artifacts_tree_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        path: Annotated[
            Optional[StrictStr], Field(description="Path query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run artifacts tree  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_artifacts_tree_with_http_info(namespace, owner, project, uuid, path, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param path: Path query param.
        :type path: str
        :param connection: Connection query param.
        :type connection: str
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
        :rtype: tuple(V1ArtifactTree, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["namespace", "owner", "project", "uuid", "path", "connection"]
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
                    " to method get_run_artifacts_tree" % _key
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
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
            "200": "V1ArtifactTree",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/artifacts/tree",
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
    def get_run_clones_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
    ) -> V1ListRunsResponse:  # noqa: E501
        """Get run clones lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_clones_lineage(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: V1ListRunsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_clones_lineage_with_http_info(
            owner, entity, uuid, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_clones_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        """Get run clones lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_clones_lineage_with_http_info(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: tuple(V1ListRunsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "entity",
            "uuid",
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
                    " to method get_run_clones_lineage" % _key
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
            "200": "V1ListRunsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/lineage/clones",
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
    def get_run_connections_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
    ) -> V1ListRunConnectionsResponse:  # noqa: E501
        """Get run connections lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_connections_lineage(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: V1ListRunConnectionsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_connections_lineage_with_http_info(
            owner, entity, uuid, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_connections_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        """Get run connections lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_connections_lineage_with_http_info(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: tuple(V1ListRunConnectionsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "entity",
            "uuid",
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
                    " to method get_run_connections_lineage" % _key
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
            "200": "V1ListRunConnectionsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/lineage/connections",
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
    def get_run_downstream_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
    ) -> V1ListRunEdgesResponse:  # noqa: E501
        """Get run downstream lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_downstream_lineage(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: V1ListRunEdgesResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_downstream_lineage_with_http_info(
            owner, entity, uuid, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_downstream_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        """Get run downstream lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_downstream_lineage_with_http_info(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: tuple(V1ListRunEdgesResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "entity",
            "uuid",
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
                    " to method get_run_downstream_lineage" % _key
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
            "200": "V1ListRunEdgesResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/lineage/downstream",
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
    def get_run_events(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        kind: Annotated[str, Field(..., description="The artifact kind")],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        orient: Annotated[
            Optional[StrictStr], Field(description="Orient query param.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ) -> V1EventsResponse:  # noqa: E501
        """Get run events  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_events(namespace, owner, project, uuid, kind, names, orient, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param kind: The artifact kind (required)
        :type kind: str
        :param names: Names query param.
        :type names: str
        :param orient: Orient query param.
        :type orient: str
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection query param.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        :rtype: V1EventsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_events_with_http_info(
            namespace,
            owner,
            project,
            uuid,
            kind,
            names,
            orient,
            force,
            sample,
            connection,
            status,
            **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_events_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        kind: Annotated[str, Field(..., description="The artifact kind")],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        orient: Annotated[
            Optional[StrictStr], Field(description="Orient query param.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run events  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_events_with_http_info(namespace, owner, project, uuid, kind, names, orient, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param kind: The artifact kind (required)
        :type kind: str
        :param names: Names query param.
        :type names: str
        :param orient: Orient query param.
        :type orient: str
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection query param.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        :rtype: tuple(V1EventsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "kind",
            "names",
            "orient",
            "force",
            "sample",
            "connection",
            "status",
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
                    " to method get_run_events" % _key
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
        if _params["kind"]:
            _path_params["kind"] = _params["kind"]

        # process the query parameters
        _query_params = []
        if _params.get("names") is not None:  # noqa: E501
            _query_params.append(("names", _params["names"]))
        if _params.get("orient") is not None:  # noqa: E501
            _query_params.append(("orient", _params["orient"]))
        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))
        if _params.get("sample") is not None:  # noqa: E501
            _query_params.append(("sample", _params["sample"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))
        if _params.get("status") is not None:  # noqa: E501
            _query_params.append(("status", _params["status"]))

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
            "200": "V1EventsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/events/{kind}",
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
    def get_run_logs(
        self,
        namespace: StrictStr,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        last_time: Annotated[
            Optional[datetime], Field(description="last time.")
        ] = None,
        last_file: Annotated[
            Optional[StrictStr], Field(description="last file.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ) -> V1Logs:  # noqa: E501
        """Get run logs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_logs(namespace, owner, project, uuid, last_time, last_file, force, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param last_time: last time.
        :type last_time: datetime
        :param last_file: last file.
        :type last_file: str
        :param force: Force query param.
        :type force: bool
        :param connection: Connection to use.
        :type connection: str
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
        :rtype: V1Logs
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_logs_with_http_info(
            namespace,
            owner,
            project,
            uuid,
            last_time,
            last_file,
            force,
            connection,
            **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_logs_with_http_info(
        self,
        namespace: StrictStr,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        last_time: Annotated[
            Optional[datetime], Field(description="last time.")
        ] = None,
        last_file: Annotated[
            Optional[StrictStr], Field(description="last file.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run logs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_logs_with_http_info(namespace, owner, project, uuid, last_time, last_file, force, connection, async_req=True)
        >>> result = thread.get()

        :param namespace: (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param last_time: last time.
        :type last_time: datetime
        :param last_file: last file.
        :type last_file: str
        :param force: Force query param.
        :type force: bool
        :param connection: Connection to use.
        :type connection: str
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
        :rtype: tuple(V1Logs, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "last_time",
            "last_file",
            "force",
            "connection",
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
                    " to method get_run_logs" % _key
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
        if _params.get("last_time") is not None:  # noqa: E501
            if isinstance(_params["last_time"], datetime):
                _query_params.append(
                    (
                        "last_time",
                        _params["last_time"].strftime(
                            self.api_client.configuration.datetime_format
                        ),
                    )
                )
            else:
                _query_params.append(("last_time", _params["last_time"]))
        if _params.get("last_file") is not None:  # noqa: E501
            _query_params.append(("last_file", _params["last_file"]))
        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
            "200": "V1Logs",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/logs",
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
    def get_run_namespace(
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
        **kwargs
    ) -> V1RunSettings:  # noqa: E501
        """Get Run namespace  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_namespace(owner, entity, uuid, async_req=True)
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
        :rtype: V1RunSettings
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_namespace_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_namespace_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Get Run namespace  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_namespace_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: tuple(V1RunSettings, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_run_namespace" % _key
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
            "200": "V1RunSettings",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/namespace",
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
    def get_run_resources(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        tail: Annotated[
            Optional[bool], Field(description="Query param flag to tail the values.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ) -> V1EventsResponse:  # noqa: E501
        """Get run resources events  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_resources(namespace, owner, project, uuid, names, tail, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param names: Names query param.
        :type names: str
        :param tail: Query param flag to tail the values.
        :type tail: bool
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection query param.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        :rtype: V1EventsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_resources_with_http_info(
            namespace,
            owner,
            project,
            uuid,
            names,
            tail,
            force,
            sample,
            connection,
            status,
            **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_resources_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        tail: Annotated[
            Optional[bool], Field(description="Query param flag to tail the values.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection query param.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Get run resources events  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_resources_with_http_info(namespace, owner, project, uuid, names, tail, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param names: Names query param.
        :type names: str
        :param tail: Query param flag to tail the values.
        :type tail: bool
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection query param.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        :rtype: tuple(V1EventsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "namespace",
            "owner",
            "project",
            "uuid",
            "names",
            "tail",
            "force",
            "sample",
            "connection",
            "status",
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
                    " to method get_run_resources" % _key
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
        if _params.get("names") is not None:  # noqa: E501
            _query_params.append(("names", _params["names"]))
        if _params.get("tail") is not None:  # noqa: E501
            _query_params.append(("tail", _params["tail"]))
        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))
        if _params.get("sample") is not None:  # noqa: E501
            _query_params.append(("sample", _params["sample"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))
        if _params.get("status") is not None:  # noqa: E501
            _query_params.append(("status", _params["status"]))

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
            "200": "V1EventsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/resources",
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
    def get_run_settings(
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
        **kwargs
    ) -> V1RunSettings:  # noqa: E501
        """Get Run settings  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_settings(owner, entity, uuid, async_req=True)
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
        :rtype: V1RunSettings
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_settings_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_settings_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Get Run settings  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_settings_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: tuple(V1RunSettings, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_run_settings" % _key
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
            "200": "V1RunSettings",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/settings",
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
    def get_run_stats(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        **kwargs
    ) -> object:  # noqa: E501
        """Get run stats  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_stats(owner, entity, uuid, offset, limit, sort, query, bookmarks, mode, kind, aggregate, groupby, trunc, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        return self.get_run_stats_with_http_info(
            owner,
            entity,
            uuid,
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
            **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_stats_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        **kwargs
    ):  # noqa: E501
        """Get run stats  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_stats_with_http_info(owner, entity, uuid, offset, limit, sort, query, bookmarks, mode, kind, aggregate, groupby, trunc, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
            "entity",
            "uuid",
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
                    " to method get_run_stats" % _key
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
            "/api/v1/{owner}/{entity}/runs/{uuid}/stats",
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
    def get_run_statuses(
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
        **kwargs
    ) -> V1Status:  # noqa: E501
        """Get run statuses  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_statuses(owner, entity, uuid, async_req=True)
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
        :rtype: V1Status
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_statuses_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_statuses_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Get run statuses  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_statuses_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: tuple(V1Status, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_run_statuses" % _key
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
            "200": "V1Status",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/statuses",
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
    def get_run_upstream_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
    ) -> V1ListRunEdgesResponse:  # noqa: E501
        """Get run upstream lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_upstream_lineage(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: V1ListRunEdgesResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_run_upstream_lineage_with_http_info(
            owner, entity, uuid, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_run_upstream_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        entity: Annotated[
            StrictStr, Field(..., description="Entity name under namespace")
        ],
        uuid: Annotated[StrictStr, Field(..., description="SubEntity uuid")],
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
        """Get run upstream lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_run_upstream_lineage_with_http_info(owner, entity, uuid, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param entity: Entity name under namespace (required)
        :type entity: str
        :param uuid: SubEntity uuid (required)
        :type uuid: str
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
        :rtype: tuple(V1ListRunEdgesResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            "owner",
            "entity",
            "uuid",
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
                    " to method get_run_upstream_lineage" % _key
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
            "200": "V1ListRunEdgesResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/lineage/upstream",
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
    def get_runs_artifacts_lineage(
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
    ) -> V1ListRunArtifactsResponse:  # noqa: E501
        """Get runs artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_runs_artifacts_lineage(owner, name, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: V1ListRunArtifactsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.get_runs_artifacts_lineage_with_http_info(
            owner, name, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def get_runs_artifacts_lineage_with_http_info(
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
        """Get runs artifacts lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_runs_artifacts_lineage_with_http_info(owner, name, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: tuple(V1ListRunArtifactsResponse, status_code(int), headers(HTTPHeaderDict))
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
                    " to method get_runs_artifacts_lineage" % _key
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
            "200": "V1ListRunArtifactsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{name}/runs/lineage/artifacts",
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
    def impersonate_token(
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
        **kwargs
    ) -> V1Auth:  # noqa: E501
        """Impersonate run token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.impersonate_token(owner, entity, uuid, async_req=True)
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
        :rtype: V1Auth
        """
        kwargs["_return_http_data_only"] = True
        return self.impersonate_token_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def impersonate_token_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Impersonate run token  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.impersonate_token_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: tuple(V1Auth, status_code(int), headers(HTTPHeaderDict))
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
                    " to method impersonate_token" % _key
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
            "200": "V1Auth",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/impersonate",
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
    def inspect_run(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        tail: Annotated[
            Optional[bool], Field(description="Query param flag to tail the values.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ) -> object:  # noqa: E501
        """Inspect an active run full conditions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.inspect_run(namespace, owner, project, uuid, names, tail, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param names: Names query param.
        :type names: str
        :param tail: Query param flag to tail the values.
        :type tail: bool
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection to use.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
        return self.inspect_run_with_http_info(
            namespace,
            owner,
            project,
            uuid,
            names,
            tail,
            force,
            sample,
            connection,
            status,
            **kwargs
        )  # noqa: E501

    @validate_arguments
    def inspect_run_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="namespace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        names: Annotated[
            Optional[StrictStr], Field(description="Names query param.")
        ] = None,
        tail: Annotated[
            Optional[bool], Field(description="Query param flag to tail the values.")
        ] = None,
        force: Annotated[
            Optional[bool], Field(description="Force query param.")
        ] = None,
        sample: Annotated[
            Optional[StrictInt], Field(description="Sample query param.")
        ] = None,
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        status: Annotated[
            Optional[StrictStr], Field(description="Optional status.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Inspect an active run full conditions  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.inspect_run_with_http_info(namespace, owner, project, uuid, names, tail, force, sample, connection, status, async_req=True)
        >>> result = thread.get()

        :param namespace: namespace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param names: Names query param.
        :type names: str
        :param tail: Query param flag to tail the values.
        :type tail: bool
        :param force: Force query param.
        :type force: bool
        :param sample: Sample query param.
        :type sample: int
        :param connection: Connection to use.
        :type connection: str
        :param status: Optional status.
        :type status: str
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
            "namespace",
            "owner",
            "project",
            "uuid",
            "names",
            "tail",
            "force",
            "sample",
            "connection",
            "status",
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
                    " to method inspect_run" % _key
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
        if _params.get("names") is not None:  # noqa: E501
            _query_params.append(("names", _params["names"]))
        if _params.get("tail") is not None:  # noqa: E501
            _query_params.append(("tail", _params["tail"]))
        if _params.get("force") is not None:  # noqa: E501
            _query_params.append(("force", _params["force"]))
        if _params.get("sample") is not None:  # noqa: E501
            _query_params.append(("sample", _params["sample"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))
        if _params.get("status") is not None:  # noqa: E501
            _query_params.append(("status", _params["status"]))

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
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/k8s_inspect",
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
    def invalidate_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Invalidate run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.invalidate_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.invalidate_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def invalidate_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Invalidate run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.invalidate_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method invalidate_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/invalidate",
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
    def invalidate_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Invalidate runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.invalidate_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.invalidate_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def invalidate_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Invalidate runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.invalidate_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method invalidate_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/invalidate",
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
    def list_archived_runs(
        self,
        user: Annotated[StrictStr, Field(..., description="User")],
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
    ) -> V1ListRunsResponse:  # noqa: E501
        """List archived runs for user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_archived_runs(user, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param user: User (required)
        :type user: str
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
        :rtype: V1ListRunsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_archived_runs_with_http_info(
            user, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_archived_runs_with_http_info(
        self,
        user: Annotated[StrictStr, Field(..., description="User")],
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
        """List archived runs for user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_archived_runs_with_http_info(user, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param user: User (required)
        :type user: str
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
        :rtype: tuple(V1ListRunsResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["user", "offset", "limit", "sort", "query", "no_page"]
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
                    " to method list_archived_runs" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["user"]:
            _path_params["user"] = _params["user"]

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
            "200": "V1ListRunsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/archives/{user}/runs",
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
    def list_bookmarked_runs(
        self,
        user: Annotated[StrictStr, Field(..., description="User")],
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
    ) -> V1ListBookmarksResponse:  # noqa: E501
        """List bookmarked runs for user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_bookmarked_runs(user, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param user: User (required)
        :type user: str
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
        :rtype: V1ListBookmarksResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_bookmarked_runs_with_http_info(
            user, offset, limit, sort, query, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_bookmarked_runs_with_http_info(
        self,
        user: Annotated[StrictStr, Field(..., description="User")],
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
        """List bookmarked runs for user  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_bookmarked_runs_with_http_info(user, offset, limit, sort, query, no_page, async_req=True)
        >>> result = thread.get()

        :param user: User (required)
        :type user: str
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
        :rtype: tuple(V1ListBookmarksResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["user", "offset", "limit", "sort", "query", "no_page"]
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
                    " to method list_bookmarked_runs" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["user"]:
            _path_params["user"] = _params["user"]

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
            "200": "V1ListBookmarksResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/bookmarks/{user}/runs",
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
    def list_runs(
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
    ) -> V1ListRunsResponse:  # noqa: E501
        """List runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_runs(owner, name, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: V1ListRunsResponse
        """
        kwargs["_return_http_data_only"] = True
        return self.list_runs_with_http_info(
            owner, name, offset, limit, sort, query, bookmarks, mode, no_page, **kwargs
        )  # noqa: E501

    @validate_arguments
    def list_runs_with_http_info(
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
        """List runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_runs_with_http_info(owner, name, offset, limit, sort, query, bookmarks, mode, no_page, async_req=True)
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
        :rtype: tuple(V1ListRunsResponse, status_code(int), headers(HTTPHeaderDict))
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
                    " to method list_runs" % _key
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
            "200": "V1ListRunsResponse",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{name}/runs",
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
    def notify_run_status(
        self,
        namespace: Annotated[StrictStr, Field(..., description="Na,espace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        body: V1EntityNotificationBody,
        **kwargs
    ) -> None:  # noqa: E501
        """Notify run status  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.notify_run_status(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: Na,espace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param body: (required)
        :type body: V1EntityNotificationBody
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
        return self.notify_run_status_with_http_info(
            namespace, owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def notify_run_status_with_http_info(
        self,
        namespace: Annotated[StrictStr, Field(..., description="Na,espace")],
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        uuid: Annotated[
            StrictStr, Field(..., description="Uuid identifier of the entity")
        ],
        body: V1EntityNotificationBody,
        **kwargs
    ):  # noqa: E501
        """Notify run status  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.notify_run_status_with_http_info(namespace, owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param namespace: Na,espace (required)
        :type namespace: str
        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param uuid: Uuid identifier of the entity (required)
        :type uuid: str
        :param body: (required)
        :type body: V1EntityNotificationBody
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
                    " to method notify_run_status" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/streams/v1/{namespace}/{owner}/{project}/runs/{uuid}/notify",
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
    def patch_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Patch run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_run(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.patch_run_with_http_info(
            owner, project, run_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def patch_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Patch run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.patch_run_with_http_info(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "run_uuid", "body"]
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
                    " to method patch_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["run_uuid"]:
            _path_params["run.uuid"] = _params["run_uuid"]

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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{run.uuid}",
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
    def restart_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Restart run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.restart_run(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.restart_run_with_http_info(
            owner, project, run_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def restart_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Restart run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.restart_run_with_http_info(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "run_uuid", "body"]
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
                    " to method restart_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["run_uuid"]:
            _path_params["run.uuid"] = _params["run_uuid"]

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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{run.uuid}/restart",
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
    def restore_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Restore run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.restore_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.restore_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def restore_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Restore run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.restore_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method restore_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/restore",
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
    def restore_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Restore runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.restore_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.restore_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def restore_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Restore runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.restore_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method restore_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/restore",
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
    def resume_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Resume run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.resume_run(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.resume_run_with_http_info(
            owner, project, run_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def resume_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Resume run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.resume_run_with_http_info(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "run_uuid", "body"]
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
                    " to method resume_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["run_uuid"]:
            _path_params["run.uuid"] = _params["run_uuid"]

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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{run.uuid}/resume",
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
    def set_run_edges_lineage(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[StrictStr, Field(..., description="Project")],
        uuid: Annotated[StrictStr, Field(..., description="Run uuid")],
        body: Annotated[V1RunEdgesGraph, Field(..., description="Run edges graph")],
        **kwargs
    ) -> None:  # noqa: E501
        """Set run edges graph lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.set_run_edges_lineage(owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project (required)
        :type project: str
        :param uuid: Run uuid (required)
        :type uuid: str
        :param body: Run edges graph (required)
        :type body: V1RunEdgesGraph
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
        return self.set_run_edges_lineage_with_http_info(
            owner, project, uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def set_run_edges_lineage_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[StrictStr, Field(..., description="Project")],
        uuid: Annotated[StrictStr, Field(..., description="Run uuid")],
        body: Annotated[V1RunEdgesGraph, Field(..., description="Run edges graph")],
        **kwargs
    ):  # noqa: E501
        """Set run edges graph lineage  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.set_run_edges_lineage_with_http_info(owner, project, uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project (required)
        :type project: str
        :param uuid: Run uuid (required)
        :type uuid: str
        :param body: Run edges graph (required)
        :type body: V1RunEdgesGraph
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

        _all_params = ["owner", "project", "uuid", "body"]
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
                    " to method set_run_edges_lineage" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{uuid}/lineage/edges",
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
    def skip_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Skip run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.skip_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.skip_run_with_http_info(owner, entity, uuid, **kwargs)  # noqa: E501

    @validate_arguments
    def skip_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Skip run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.skip_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method skip_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/skip",
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
    def skip_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Skip runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.skip_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.skip_runs_with_http_info(owner, name, body, **kwargs)  # noqa: E501

    @validate_arguments
    def skip_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Skip runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.skip_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method skip_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/skip",
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
    def stop_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Stop run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.stop_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.stop_run_with_http_info(owner, entity, uuid, **kwargs)  # noqa: E501

    @validate_arguments
    def stop_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Stop run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.stop_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method stop_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/stop",
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
    def stop_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ) -> None:  # noqa: E501
        """Stop runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.stop_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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
        return self.stop_runs_with_http_info(owner, name, body, **kwargs)  # noqa: E501

    @validate_arguments
    def stop_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1Uuids, Field(..., description="Uuids of the entities")],
        **kwargs
    ):  # noqa: E501
        """Stop runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.stop_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Uuids of the entities (required)
        :type body: V1Uuids
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

        _all_params = ["owner", "name", "body"]
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
                    " to method stop_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/stop",
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
    def sync_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> None:  # noqa: E501
        """Sync offline run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.sync_run(owner, project, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param body: Run object (required)
        :type body: V1Run
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
        return self.sync_run_with_http_info(
            owner, project, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def sync_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Sync offline run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.sync_run_with_http_info(owner, project, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param body: Run object (required)
        :type body: V1Run
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

        _all_params = ["owner", "project", "body"]
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
                    " to method sync_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]

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
            "/api/v1/{owner}/{project}/runs/sync",
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
    def tag_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1EntitiesTags, Field(..., description="Data")],
        **kwargs
    ) -> None:  # noqa: E501
        """Tag runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.tag_runs(owner, project, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Data (required)
        :type body: V1EntitiesTags
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
        return self.tag_runs_with_http_info(owner, name, body, **kwargs)  # noqa: E501

    @validate_arguments
    def tag_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1EntitiesTags, Field(..., description="Data")],
        **kwargs
    ):  # noqa: E501
        """Tag runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.tag_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Data (required)
        :type body: V1EntitiesTags
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

        _all_params = ["owner", "name", "body"]
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
                    " to method tag_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/tag",
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
    def transfer_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> None:  # noqa: E501
        """Transfer run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.transfer_run(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        return self.transfer_run_with_http_info(
            owner, project, run_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def transfer_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Transfer run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.transfer_run_with_http_info(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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

        _all_params = ["owner", "project", "run_uuid", "body"]
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
                    " to method transfer_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["run_uuid"]:
            _path_params["run.uuid"] = _params["run_uuid"]

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
            "/api/v1/{owner}/{project}/runs/{run.uuid}/transfer",
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
    def transfer_runs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1EntitiesTransfer, Field(..., description="Data")],
        **kwargs
    ) -> None:  # noqa: E501
        """Transfer runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.transfer_runs(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Data (required)
        :type body: V1EntitiesTransfer
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
        return self.transfer_runs_with_http_info(
            owner, name, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def transfer_runs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        name: Annotated[StrictStr, Field(..., description="Entity under namespace")],
        body: Annotated[V1EntitiesTransfer, Field(..., description="Data")],
        **kwargs
    ):  # noqa: E501
        """Transfer runs  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.transfer_runs_with_http_info(owner, name, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param name: Entity under namespace (required)
        :type name: str
        :param body: Data (required)
        :type body: V1EntitiesTransfer
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

        _all_params = ["owner", "name", "body"]
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
                    " to method transfer_runs" % _key
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
            "/api/v1/{owner}/{name}/runs/transfer",
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
    def unbookmark_run(
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
        **kwargs
    ) -> None:  # noqa: E501
        """Unbookmark run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.unbookmark_run(owner, entity, uuid, async_req=True)
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
        :rtype: None
        """
        kwargs["_return_http_data_only"] = True
        return self.unbookmark_run_with_http_info(
            owner, entity, uuid, **kwargs
        )  # noqa: E501

    @validate_arguments
    def unbookmark_run_with_http_info(
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
        **kwargs
    ):  # noqa: E501
        """Unbookmark run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.unbookmark_run_with_http_info(owner, entity, uuid, async_req=True)
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
        :rtype: None
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
                    " to method unbookmark_run" % _key
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

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{entity}/runs/{uuid}/unbookmark",
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
    def update_run(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ) -> V1Run:  # noqa: E501
        """Update run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_run(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: V1Run
        """
        kwargs["_return_http_data_only"] = True
        return self.update_run_with_http_info(
            owner, project, run_uuid, body, **kwargs
        )  # noqa: E501

    @validate_arguments
    def update_run_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project where the run will be assigned")
        ],
        run_uuid: Annotated[StrictStr, Field(..., description="UUID")],
        body: Annotated[V1Run, Field(..., description="Run object")],
        **kwargs
    ):  # noqa: E501
        """Update run  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_run_with_http_info(owner, project, run_uuid, body, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project where the run will be assigned (required)
        :type project: str
        :param run_uuid: UUID (required)
        :type run_uuid: str
        :param body: Run object (required)
        :type body: V1Run
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
        :rtype: tuple(V1Run, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = ["owner", "project", "run_uuid", "body"]
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
                    " to method update_run" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params["owner"]:
            _path_params["owner"] = _params["owner"]
        if _params["project"]:
            _path_params["project"] = _params["project"]
        if _params["run_uuid"]:
            _path_params["run.uuid"] = _params["run_uuid"]

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
            "200": "V1Run",
            "204": "object",
            "403": "object",
            "404": "object",
        }

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{run.uuid}",
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
    def upload_run_artifact(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project having access to the store")
        ],
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
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ) -> None:  # noqa: E501
        """Upload an artifact file to a store via run access  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_run_artifact(owner, project, uuid, uploadfile, path, overwrite, connection, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project having access to the store (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param uploadfile: The file to upload. (required)
        :type uploadfile: bytearray
        :param path: File path query params.
        :type path: str
        :param overwrite: File path query params.
        :type overwrite: bool
        :param connection: Connection to use.
        :type connection: str
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
        return self.upload_run_artifact_with_http_info(
            owner, project, uuid, uploadfile, path, overwrite, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def upload_run_artifact_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project having access to the store")
        ],
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
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Upload an artifact file to a store via run access  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_run_artifact_with_http_info(owner, project, uuid, uploadfile, path, overwrite, connection, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project having access to the store (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param uploadfile: The file to upload. (required)
        :type uploadfile: bytearray
        :param path: File path query params.
        :type path: str
        :param overwrite: File path query params.
        :type overwrite: bool
        :param connection: Connection to use.
        :type connection: str
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

        _all_params = [
            "owner",
            "project",
            "uuid",
            "uploadfile",
            "path",
            "overwrite",
            "connection",
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
                    " to method upload_run_artifact" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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
        if _params.get("overwrite") is not None:  # noqa: E501
            _query_params.append(("overwrite", _params["overwrite"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["multipart/form-data"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{uuid}/artifacts/upload",
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
    def upload_run_logs(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project having access to the store")
        ],
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
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ) -> None:  # noqa: E501
        """Upload a logs file to a store via run access  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_run_logs(owner, project, uuid, uploadfile, path, overwrite, connection, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project having access to the store (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param uploadfile: The file to upload. (required)
        :type uploadfile: bytearray
        :param path: File path query params.
        :type path: str
        :param overwrite: File path query params.
        :type overwrite: bool
        :param connection: Connection to use.
        :type connection: str
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
        return self.upload_run_logs_with_http_info(
            owner, project, uuid, uploadfile, path, overwrite, connection, **kwargs
        )  # noqa: E501

    @validate_arguments
    def upload_run_logs_with_http_info(
        self,
        owner: Annotated[StrictStr, Field(..., description="Owner of the namespace")],
        project: Annotated[
            StrictStr, Field(..., description="Project having access to the store")
        ],
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
        connection: Annotated[
            Optional[StrictStr], Field(description="Connection to use.")
        ] = None,
        **kwargs
    ):  # noqa: E501
        """Upload a logs file to a store via run access  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_run_logs_with_http_info(owner, project, uuid, uploadfile, path, overwrite, connection, async_req=True)
        >>> result = thread.get()

        :param owner: Owner of the namespace (required)
        :type owner: str
        :param project: Project having access to the store (required)
        :type project: str
        :param uuid: Unique integer identifier of the entity (required)
        :type uuid: str
        :param uploadfile: The file to upload. (required)
        :type uploadfile: bytearray
        :param path: File path query params.
        :type path: str
        :param overwrite: File path query params.
        :type overwrite: bool
        :param connection: Connection to use.
        :type connection: str
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

        _all_params = [
            "owner",
            "project",
            "uuid",
            "uploadfile",
            "path",
            "overwrite",
            "connection",
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
                    " to method upload_run_logs" % _key
                )
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
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
        if _params.get("overwrite") is not None:  # noqa: E501
            _query_params.append(("overwrite", _params["overwrite"]))
        if _params.get("connection") is not None:  # noqa: E501
            _query_params.append(("connection", _params["connection"]))

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
        )  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get(
            "_content_type",
            self.api_client.select_header_content_type(["multipart/form-data"]),
        )
        if _content_types_list:
            _header_params["Content-Type"] = _content_types_list

        # authentication setting
        _auth_settings = ["ApiKey"]  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            "/api/v1/{owner}/{project}/runs/{uuid}/logs/upload",
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
