import sys

from typing import Any, Dict, Optional

from clipped.config.exceptions import ClippedException, SchemaError

PolyaxonException = ClippedException
PolyaxonSchemaError = SchemaError


class OpenApiException(PolyaxonException):
    """The base exception class for all OpenAPIExceptions"""


class ApiTypeError(OpenApiException, TypeError):
    def __init__(self, msg, path_to_item=None, valid_classes=None, key_type=None):
        """Raises an exception for TypeErrors

        Args:
            msg (str): the exception message

        Keyword Args:
            path_to_item (list): a list of keys an indices to get to the
                                 current_item
                                 None if unset
            valid_classes (tuple): the primitive classes that current item
                                   should be an instance of
                                   None if unset
            key_type (bool): False if our value is a value in a dict
                             True if it is a key in a dict
                             False if our item is an item in a list
                             None if unset
        """
        self.path_to_item = path_to_item
        self.valid_classes = valid_classes
        self.key_type = key_type
        full_msg = msg
        if path_to_item:
            full_msg = "{0} at {1}".format(msg, render_path(path_to_item))
        super(ApiTypeError, self).__init__(full_msg)


class ApiValueError(OpenApiException, ValueError):
    def __init__(self, msg, path_to_item=None):
        """
        Args:
            msg (str): the exception message

        Keyword Args:
            path_to_item (list) the path to the exception in the
                received_data dict. None if unset
        """

        self.path_to_item = path_to_item
        full_msg = msg
        if path_to_item:
            full_msg = "{0} at {1}".format(msg, render_path(path_to_item))
        super(ApiValueError, self).__init__(full_msg)


class ApiKeyError(OpenApiException, KeyError):
    def __init__(self, msg, path_to_item=None):
        """
        Args:
            msg (str): the exception message

        Keyword Args:
            path_to_item (None/list) the path to the exception in the
                received_data dict
        """
        self.path_to_item = path_to_item
        full_msg = msg
        if path_to_item:
            full_msg = "{0} at {1}".format(msg, render_path(path_to_item))
        super(ApiKeyError, self).__init__(full_msg)


class ApiException(OpenApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        if http_resp:
            self.status = http_resp.status
            self.reason = http_resp.reason
            self.body = http_resp.data
            self.headers = http_resp.getheaders()
        else:
            self.status = status
            self.reason = reason
            self.body = None
            self.headers = None

    def __str__(self):
        """Custom error messages for exception"""
        error_message = "({0})\n" "Reason: {1}\n".format(self.status, self.reason)
        if self.headers:
            error_message += "HTTP response headers: {0}\n".format(self.headers)

        if self.body:
            error_message += "HTTP response body: {0}\n".format(self.body)

        return error_message


class NotFoundException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        super(NotFoundException, self).__init__(status, reason, http_resp)


class UnauthorizedException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        super(UnauthorizedException, self).__init__(status, reason, http_resp)


class ForbiddenException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        super(ForbiddenException, self).__init__(status, reason, http_resp)


class ServiceException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        super(ServiceException, self).__init__(status, reason, http_resp)


def render_path(path_to_item):
    """Returns a string representation of a path"""
    result = ""
    for pth in path_to_item:
        if isinstance(pth, int):
            result += "[{0}]".format(pth)
        else:
            result += "['{0}']".format(pth)
    return result


def handle_api_error(
    e,
    logger: Any,
    message: Optional[str] = None,
    http_messages_mapping: Optional[Dict] = None,
    sys_exit: bool = False,
):
    if http_messages_mapping:
        http_messages_mapping.update(HTTP_ERROR_MESSAGES_MAPPING)
    else:
        http_messages_mapping = HTTP_ERROR_MESSAGES_MAPPING
    if message:
        logger.error(message)
    if e and hasattr(e, "status"):
        if e.status not in http_messages_mapping.keys():
            logger.error("Exception:")
            logger.error(e, stack_info=True, exc_info=True)
        elif getattr(e, "body") and e.status != 404:
            logger.error("Error: %s" % e.body)
        if getattr(e, "reason"):
            logger.error("Reason: %s" % e.reason)
        message = http_messages_mapping.get(e.status)
        if message:
            logger.error(message)
    elif e and hasattr(e, "message"):  # Handling of HTML errors
        error_found = False
        for k in http_messages_mapping.keys():
            if str(k) in e.message:
                logger.error(http_messages_mapping.get(k))
                error_found = True
                break
        if not error_found:
            logger.error("Error:")
            logger.error(e.message)
    elif e:
        logger.error("Exception:")
        logger.error(e, stack_info=True, exc_info=True)
    if sys_exit:
        sys.exit(1)


class PolyaxonOperatorException(PolyaxonException):
    def __init__(self, cmd, args, return_code, stdout, stderr):
        self.cmd = cmd
        self.args = args
        self.return_code = return_code
        self.stdout = stdout.read() if stdout else None
        self.stderr = stderr.read()
        if stdout:
            message = "`{}` command {} failed with exit status {}\nstdout:\n{}\nstderr:\n{}".format(
                self.cmd, self.args, self.return_code, self.stdout, self.stderr
            )
        else:
            message = "`{}` command {} failed with exit status {}\nstderr:\n{}".format(
                self.cmd, self.args, self.return_code, self.stderr
            )
        super().__init__(message=message)


class PolyaxonConverterError(PolyaxonException):
    pass


class PolyaxonCompilerError(PolyaxonException):
    pass


class PolyTuneException(PolyaxonException):
    pass


class PolyaxonConfigException(PolyaxonException):
    pass


class PolyaxonK8sError(PolyaxonException):
    pass


class PolyaxonAgentError(PolyaxonException):
    pass


class PolyaxonBuildException(PolyaxonException):
    pass


class PolyaxonContainerException(Exception):
    pass


class PolyaxonConnectionError(PolyaxonException):
    pass


class PolyaxonPathException(PolyaxonException):
    pass


class PQLException(PolyaxonException):
    pass


class PolyaxonValidationError(PolyaxonSchemaError):
    pass


class PolyaxonfileError(PolyaxonSchemaError):
    pass


class PolyaxonClientException(OpenApiException):
    """The base exception class for all client exceptions"""


class PolyaxonShouldExitError(PolyaxonClientException):
    pass


class PolyaxonHTTPError(PolyaxonClientException):
    def __init__(self, endpoint, response, message=None, status_code=None):
        super().__init__()
        self.endpoint = endpoint
        self.response = response
        self.message = getattr(self, "message", message)
        self.status_code = getattr(self, "status_code", status_code)

    def __str__(self):
        return "{status_code} on {endpoint}.".format(
            status_code=self.status_code, endpoint=self.endpoint
        )


HTTP_ERROR_MESSAGES_MAPPING = {
    400: "Status: 400. One or more request parameters are incorrect",
    401: "Status: 401. Authentication failed. Retry by invoking Polyaxon login.",
    403: "Status: 403. You are not authorized to access this resource on Polyaxon.",
    404: "Status: 404. "
    "The resource you are looking for was not found. Check if the name or uuid is correct.",
    405: "Status: 405. Endpoint does not exist or not configured on this API, "
    "make sure you are connecting to the correct host.",
    429: "Status: 429. You are over the allowed limits for this operation.",
    500: "Status: 502. Internal server error, please try again later.",
    502: "Status: 502. Invalid response from Polyaxon server.",
    503: "Status: 503. A problem was encountered, please try again later.",
    504: "Status: 504. Polyaxon server took too long to respond.",
    525: "Status: 525. SSL error.",
}


def handle_api_error(
    e,
    logger: Any,
    message: Optional[str] = None,
    http_messages_mapping: Optional[Dict] = None,
    sys_exit: bool = False,
):
    if http_messages_mapping:
        http_messages_mapping.update(HTTP_ERROR_MESSAGES_MAPPING)
    else:
        http_messages_mapping = HTTP_ERROR_MESSAGES_MAPPING
    if message:
        logger.error(message)
    if e and hasattr(e, "status"):
        if e.status not in http_messages_mapping.keys():
            logger.error("Exception:")
            logger.error(e, stack_info=True, exc_info=True)
        elif getattr(e, "body") and e.status != 404:
            logger.error("Error: %s" % e.body)
        if getattr(e, "reason"):
            logger.error("Reason: %s" % e.reason)
        message = http_messages_mapping.get(e.status)
        if message:
            logger.error(message)
    elif e and hasattr(e, "message"):  # Handling of HTML errors
        error_found = False
        for k in http_messages_mapping.keys():
            if str(k) in e.message:
                logger.error(http_messages_mapping.get(k))
                error_found = True
                break
        if not error_found:
            logger.error("Error:")
            logger.error(e.message)
    elif e:
        logger.error("Exception:")
        logger.error(e, stack_info=True, exc_info=True)
    if sys_exit:
        sys.exit(1)
