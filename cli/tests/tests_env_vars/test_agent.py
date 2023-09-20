import os

from polyaxon._env_vars.getters import get_agent_info
from polyaxon._env_vars.keys import ENV_KEYS_AGENT_INSTANCE
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonAgentError


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

        current = os.environ.get(ENV_KEYS_AGENT_INSTANCE)
        os.environ[ENV_KEYS_AGENT_INSTANCE] = "foo.agents.moo"
        assert get_agent_info("foo.agents.moo") == ("foo", "moo")
        if current:
            os.environ[ENV_KEYS_AGENT_INSTANCE] = current
        else:
            del os.environ[ENV_KEYS_AGENT_INSTANCE]
