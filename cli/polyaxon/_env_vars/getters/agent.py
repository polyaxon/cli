import os

from typing import Optional, Tuple

from polyaxon._env_vars.keys import (
    ENV_KEYS_AGENT_INSTANCE,
    ENV_KEYS_ARTIFACTS_STORE_NAME,
)
from polyaxon.exceptions import PolyaxonAgentError


def get_agent_info(agent_instance: Optional[str] = None) -> Tuple[str, str]:
    agent_instance = agent_instance or os.getenv(ENV_KEYS_AGENT_INSTANCE, None)
    if not agent_instance:
        raise PolyaxonAgentError(
            "Could get agent info, "
            "please make sure that this agent was registered in Polyaxon."
        )

    parts = agent_instance.split(".")
    if not len(parts) == 3 or parts[1] != "agents":
        raise PolyaxonAgentError(
            "agent instance is invalid `{}`, "
            "please make sure that this agent was registered in Polyaxon.".format(
                agent_instance
            )
        )
    return parts[0], parts[-1]


def get_artifacts_store_name(default: Optional[str] = "artifacts_store"):
    """Get the artifacts store name"""
    return os.getenv(ENV_KEYS_ARTIFACTS_STORE_NAME, default)
