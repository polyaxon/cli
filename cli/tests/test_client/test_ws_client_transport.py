import mock
import pytest

from polyaxon._client.transport import ws_client
from polyaxon._sdk.configuration import Configuration
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


@pytest.mark.client_mark
class TestWSClientTransport(BaseTestCase):
    def test_get_websocket_url(self):
        assert (
            ws_client.get_websocket_url("http://localhost:8000/exec")
            == "ws://localhost:8000/exec"
        )
        assert (
            ws_client.get_websocket_url(
                "https://polyaxon.com/exec",
                query_params=[("command", ["/bin/bash", "-l"]), ("tty", True)],
            )
            == "wss://polyaxon.com/exec?command=%2Fbin%2Fbash&command=-l&tty=True"
        )

    @mock.patch("polyaxon._vendor.k8s.ws_client.WebSocket")
    def test_websocket_call_through_proxy(self, websocket):
        # The SDK configuration has no `no_proxy`
        configuration = Configuration(host="https://polyaxon.com")
        configuration.proxy = "http://proxy.local:3128"

        client = ws_client.websocket_call(
            configuration,
            "https://polyaxon.com/exec",
            headers={"authorization": "token foo"},
        )

        assert isinstance(client, ws_client.WSClient)
        connect = websocket.return_value.connect
        assert connect.call_args.args == ("wss://polyaxon.com/exec",)
        assert connect.call_args.kwargs["http_proxy_host"] == "proxy.local"
        assert connect.call_args.kwargs["http_proxy_port"] == 3128
        assert "authorization: token foo" in connect.call_args.kwargs["header"]

    @mock.patch("polyaxon._vendor.k8s.ws_client.WebSocket")
    def test_websocket_call_raises_client_exception(self, websocket):
        websocket.return_value.connect.side_effect = ConnectionRefusedError("refused")

        with pytest.raises(PolyaxonClientException):
            ws_client.websocket_call(
                Configuration(host="https://polyaxon.com"),
                "https://polyaxon.com/exec",
            )

    @mock.patch("polyaxon._client.transport.ws_client.BaseWSClient.update")
    @mock.patch("polyaxon._vendor.k8s.ws_client.WebSocket")
    def test_update_pings_every_five_seconds(self, websocket, update):
        client = ws_client.WSClient(
            Configuration(host="https://polyaxon.com"),
            "wss://polyaxon.com/exec",
            headers=None,
            capture_all=True,
        )

        with mock.patch("polyaxon._client.transport.ws_client.time") as time_mock:
            time_mock.time.return_value = client.last_ping + 4
            client.update()
            websocket.return_value.ping.assert_not_called()

            time_mock.time.return_value = client.last_ping + 5
            client.update()

        websocket.return_value.ping.assert_called_once_with("PING")
        assert update.call_count == 2
