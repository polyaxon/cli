import requests

from polyaxon.client.transport import Transport
from tests.test_transports.utils import BaseTestCaseTransport


class TestHttpTransport(BaseTestCaseTransport):
    # pylint:disable=protected-access
    def setUp(self):
        super().setUp()
        self.transport = Transport()

    def test_session(self):
        assert hasattr(self.transport, "_session") is False
        assert isinstance(self.transport.session, requests.Session)
        assert isinstance(self.transport._session, requests.Session)
