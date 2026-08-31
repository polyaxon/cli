from mock import MagicMock, patch
import pytest

from polyaxon._runner.agent.exceptions import format_agent_exception
from polyaxon._runner.agent.sync_agent import BaseSyncAgent
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import ApiException, PolyaxonAgentError


pytestmark = pytest.mark.agent_mark


class ResponseMock:
    status = 500
    reason = "Internal Server Error"
    data = b'{"errors":"DefaultCredentialsError","token":"should-not-log"}'

    @staticmethod
    def getheaders():
        return {"Authorization": "should-not-log"}


class DummyAgent(BaseSyncAgent):
    EXECUTOR = MagicMock


def test_format_agent_exception_includes_api_status_reason_and_body():
    exc = ApiException(http_resp=ResponseMock())

    message = format_agent_exception(exc)

    assert "ApiException" in message
    assert "status=500" in message
    assert "reason=Internal Server Error" in message
    assert "DefaultCredentialsError" in message
    assert "should-not-log" not in message
    assert "<redacted>" in message
    assert "Authorization" not in message


def test_format_agent_exception_truncates_large_body():
    exc = ApiException(status=500, reason="Internal Server Error")
    exc.body = "x" * 20

    message = format_agent_exception(exc, max_body_length=8)

    assert "body=xxxxxxxx...<truncated 12 chars>" in message


def test_format_agent_exception_redacts_quoted_bearer_token():
    exc = ApiException(status=500, reason="Internal Server Error")
    exc.body = '{"authorization":"Bearer top-secret"}'

    message = format_agent_exception(exc)

    assert '"authorization":"<redacted>"' in message
    assert "Bearer" not in message
    assert "top-secret" not in message


def test_format_agent_exception_redacts_unquoted_bearer_token():
    exc = ApiException(status=500, reason="Internal Server Error")
    exc.body = "authorization=Bearer top-secret"

    message = format_agent_exception(exc)

    assert "authorization=<redacted>" in message
    assert "Bearer" not in message
    assert "top-secret" not in message


def test_format_agent_exception_redacts_quoted_value_with_whitespace():
    exc = ApiException(status=500, reason="Internal Server Error")
    exc.body = '{"password":"hello world"}'

    message = format_agent_exception(exc)

    assert '"password":"<redacted>"' in message
    assert "hello" not in message
    assert "world" not in message


def test_format_agent_exception_handles_generic_exception():
    message = format_agent_exception(RuntimeError("boom"))

    assert message == "RuntimeError: boom"


class TestAgentExceptionLogging(BaseTestCase):
    SET_AGENT_SETTINGS = True

    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.create_agent_status")
    @patch("polyaxon._sdk.api.agents_v1_api.AgentsV1Api.get_agent")
    def test_sync_agent_enter_uses_formatted_api_exception(
        self, get_agent, create_agent_status
    ):
        get_agent.side_effect = ApiException(http_resp=ResponseMock())
        agent = DummyAgent(owner="foo", agent_uuid="uuid")

        with pytest.raises(PolyaxonAgentError) as exc:
            agent._enter()

        message = str(exc.value)
        assert "status=500" in message
        assert "reason=Internal Server Error" in message
        assert "DefaultCredentialsError" in message
        assert "ApiException()" not in message
        create_agent_status.assert_called_once()
