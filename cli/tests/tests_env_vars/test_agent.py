import os

from polyaxon.env_vars.getters import get_agent_info
from polyaxon.env_vars.keys import EV_KEYS_AGENT_INSTANCE
from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.utils.test_utils import BaseTestCase


class TestAgentEnvVars(BaseTestCase):
    def test_get_agent_info(self):
        with self.assertRaises(PolyaxonAgentError):
            get_agent_info(None)

        with self.assertRaises(PolyaxonAgentError):
            get_agent_info("foo")

        with self.assertRaises(PolyaxonAgentError):
            get_agent_info("foo.bar")

        with self.assertRaises(PolyaxonAgentError):
            get_agent_info("foo/bar")

        with self.assertRaises(PolyaxonAgentError):
            get_agent_info("foo/bar/moo")

        with self.assertRaises(PolyaxonAgentError):
            get_agent_info("foo.bar.moo")

        assert get_agent_info("foo.agents.moo") == ("foo", "moo")

        current = os.environ.get(EV_KEYS_AGENT_INSTANCE)
        os.environ[EV_KEYS_AGENT_INSTANCE] = "foo.agents.moo"
        assert get_agent_info("foo.agents.moo") == ("foo", "moo")
        if current:
            os.environ[EV_KEYS_AGENT_INSTANCE] = current
        else:
            del os.environ[EV_KEYS_AGENT_INSTANCE]
