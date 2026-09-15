from mock import MagicMock, patch
import os
import pytest
import tempfile
from unittest import IsolatedAsyncioTestCase

from polyaxon._contexts import paths as ctx_paths
from polyaxon._runner.agent.client import AgentClient, AsyncAgentClient
from polyaxon._schemas.lifecycle import V1Statuses
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException


class ClientMock:
    def __init__(self, is_async: bool):
        self.is_async = is_async
        self.agents_v1 = MagicMock()
        self.runs_v1 = MagicMock()
        self.close_calls = 0
        self.aclose_calls = 0

    def close(self):
        self.close_calls += 1

    async def aclose(self):
        self.aclose_calls += 1


@pytest.mark.agent_mark
class TestAgentClient(BaseTestCase, IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.object(
            ctx_paths,
            "CONTEXT_USER_POLYAXON_PATH",
            os.path.join(directory.name, ".polyaxon"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    @patch("polyaxon._runner.agent.client.PolyaxonClient")
    def test_agent_client_close_closes_owned_clients(self, client_cls):
        public_client = ClientMock(is_async=False)
        internal_client = ClientMock(is_async=False)
        client_cls.side_effect = [public_client, internal_client]
        client = AgentClient(owner="foo", agent_uuid="uuid")

        assert client.client is public_client
        assert client.internal_client is internal_client

        client.close()

        assert public_client.close_calls == 1
        assert internal_client.close_calls == 1

    @patch("polyaxon._runner.agent.client.PolyaxonClient")
    async def test_agent_client_aclose_closes_owned_clients(self, client_cls):
        public_client = ClientMock(is_async=True)
        internal_client = ClientMock(is_async=True)
        client_cls.side_effect = [public_client, internal_client]
        client = AsyncAgentClient(owner="foo", agent_uuid="uuid")

        assert client.client is public_client
        assert client.internal_client is internal_client

        await client.aclose()

        assert public_client.aclose_calls == 1
        assert internal_client.aclose_calls == 1

    def test_agent_client_checks_connections_with_public_client(self):
        public_client = ClientMock(is_async=False)
        internal_client = ClientMock(is_async=False)
        client = AgentClient(
            owner="foo",
            agent_uuid="uuid",
            client=public_client,
            internal_client=internal_client,
        )

        client.check_agent_connections(namespace="agent-namespace")

        public_client.agents_v1.check_agent_connection.assert_called_once_with(
            namespace="agent-namespace",
            owner="foo",
            uuid="uuid",
            body={},
        )
        internal_client.agents_v1.check_agent_connection.assert_not_called()

    def test_agent_client_reports_failed_status_with_details(self):
        public_client = ClientMock(is_async=False)
        details = {"connection_check": {"status": "failed", "results": []}}
        client = AgentClient(
            owner="foo",
            agent_uuid="uuid",
            client=public_client,
        )

        client.log_agent_failed(
            message="Agent connection check failed.",
            reason="AgentConnectionCheck",
            meta_info=details,
        )

        call = public_client.agents_v1.create_agent_status.call_args
        assert call.kwargs["owner"] == "foo"
        assert call.kwargs["uuid"] == "uuid"
        condition = call.kwargs["body"]["condition"]
        assert condition.type == V1Statuses.FAILED
        assert condition.reason == "AgentConnectionCheck"
        assert condition.message == "Agent connection check failed."
        assert condition.meta_info == details

    def test_agent_client_close_does_not_close_injected_clients(self):
        public_client = ClientMock(is_async=False)
        internal_client = ClientMock(is_async=False)
        client = AgentClient(
            owner="foo",
            agent_uuid="uuid",
            client=public_client,
            internal_client=internal_client,
        )

        client.close()

        assert public_client.close_calls == 0
        assert internal_client.close_calls == 0

    async def test_agent_client_aclose_does_not_close_injected_clients(self):
        public_client = ClientMock(is_async=True)
        internal_client = ClientMock(is_async=True)
        client = AsyncAgentClient(
            owner="foo",
            agent_uuid="uuid",
            client=public_client,
            internal_client=internal_client,
        )

        await client.aclose()

        assert public_client.aclose_calls == 0
        assert internal_client.aclose_calls == 0

    def test_async_agent_client_does_not_expose_sync_close(self):
        client = AsyncAgentClient(owner="foo", agent_uuid="uuid")

        assert not hasattr(client, "close")

    def test_agent_client_does_not_expose_async_close(self):
        client = AgentClient(owner="foo", agent_uuid="uuid")

        assert not hasattr(client, "aclose")

    def test_agent_client_rejects_mode_mismatch_public_client(self):
        with self.assertRaises(PolyaxonClientException):
            AsyncAgentClient(
                owner="foo",
                agent_uuid="uuid",
                client=ClientMock(is_async=False),
            )

    def test_agent_client_rejects_mode_mismatch_internal_client(self):
        with self.assertRaises(PolyaxonClientException):
            AgentClient(
                owner="foo",
                agent_uuid="uuid",
                internal_client=ClientMock(is_async=True),
            )

    def test_agent_client_allows_loose_mocks_without_mode_attribute(self):
        client = AgentClient(
            owner="foo",
            agent_uuid="uuid",
            client=MagicMock(),
            internal_client=MagicMock(),
        )

        assert client.client is not None
        assert client.internal_client is not None
