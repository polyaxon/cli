import time

from kubernetes.client.rest import ApiException
from kubernetes.stream.ws_client import ERROR_CHANNEL, RESIZE_CHANNEL
from kubernetes.stream.ws_client import WSClient as BaseWSClient
from kubernetes.stream.ws_client import WSResponse, get_websocket_url

ERROR_CHANNEL = ERROR_CHANNEL
RESIZE_CHANNEL = RESIZE_CHANNEL


class WSClient(BaseWSClient):
    def __init__(self, configuration, url, headers, capture_all):
        super().__init__(
            configuration=configuration,
            url=url,
            headers=headers,
            capture_all=capture_all,
        )
        self.last_ping = time.time()

    def update(self, timeout=0):
        """Add ping logic to the original update function."""
        if time.time() - self.last_ping < 5:
            self.sock.ping("PING")
            self.last_ping = time.time()
        return super().update(timeout=timeout)


def websocket_call(configuration, url, **kwargs):
    """Customized `websocket_call` with the updated WSClient that includes a periodic ping.

    An internal function to be called in api-client when a websocket
    connection is required. method, url, and kwargs are the parameters of
    apiClient.request method.
    """

    url = get_websocket_url(url, kwargs.get("query_params"))
    headers = kwargs.get("headers")
    _request_timeout = kwargs.get("_request_timeout", 60)
    _preload_content = kwargs.get("_preload_content", False)
    capture_all = kwargs.get("capture_all", True)

    try:
        client = WSClient(configuration, url, headers, capture_all)
        if not _preload_content:
            return client
        client.run_forever(timeout=_request_timeout)
        return WSResponse("%s" % "".join(client.read_all()))
    except (Exception, KeyboardInterrupt, SystemExit) as e:
        raise ApiException(status=0, reason=str(e))
