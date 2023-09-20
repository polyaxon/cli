from polyaxon._client.transport.http_transport import HttpTransportMixin
from polyaxon._client.transport.periodic_transport import (
    PeriodicHttpTransportMixin,
    PeriodicWSTransportMixin,
)
from polyaxon._client.transport.socket_transport import SocketTransportMixin
from polyaxon._client.transport.threaded_transport import ThreadedTransportMixin


class Transport(
    HttpTransportMixin,
    PeriodicHttpTransportMixin,
    PeriodicWSTransportMixin,
    ThreadedTransportMixin,
    SocketTransportMixin,
):
    """Transport for handling http/ws operations."""

    def __init__(self, config=None):
        self.config = config

    def _get_headers(self, headers=None):
        request_headers = headers or {}
        # Auth headers if access_token is present
        if self.config:
            if "Authorization" not in request_headers and self.config.token:
                request_headers.update(
                    {
                        "Authorization": "{} {}".format(
                            self.config.authentication_type, self.config.token
                        )
                    }
                )
            if self.config.client_header:
                request_headers.update(self.config.client_header)
        return request_headers
