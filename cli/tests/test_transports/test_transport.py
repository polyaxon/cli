from polyaxon._client.transport import Transport
from polyaxon._schemas.client import ClientConfig
from polyaxon._services.auth import AuthenticationTypes
from tests.test_transports.utils import BaseTestCaseTransport


class TestTransport(BaseTestCaseTransport):
    # pylint:disable=protected-access
    def setUp(self):
        super().setUp()
        self.transport = Transport()

    def test_get_headers(self):
        assert self.transport._get_headers() == {}
        assert self.transport._get_headers({"foo": "bar"}) == {"foo": "bar"}

        self.transport.config = ClientConfig(token="token", host="host")

        assert self.transport._get_headers() == {
            "Authorization": "{} {}".format(AuthenticationTypes.TOKEN, "token")
        }
        assert self.transport._get_headers({"foo": "bar"}) == {
            "foo": "bar",
            "Authorization": "{} {}".format(AuthenticationTypes.TOKEN, "token"),
        }

        self.transport.config.authentication_type = AuthenticationTypes.INTERNAL_TOKEN
        assert self.transport._get_headers() == {
            "Authorization": "{} {}".format(AuthenticationTypes.INTERNAL_TOKEN, "token")
        }
        assert self.transport._get_headers({"foo": "bar"}) == {
            "foo": "bar",
            "Authorization": "{} {}".format(
                AuthenticationTypes.INTERNAL_TOKEN, "token"
            ),
        }
