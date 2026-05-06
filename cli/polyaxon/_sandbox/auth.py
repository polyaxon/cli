import hashlib
import hmac
import os

from polyaxon._env_vars.keys import ENV_KEYS_SECRET_INTERNAL_TOKEN
from polyaxon.exceptions import PolyaxonConverterError


DERIVATION_PREFIX = b"sandbox:v1:"


def derive_sandbox_token(signing_key: str, run_uuid: str) -> str:
    if not signing_key or not signing_key.strip():
        raise ValueError("A non-empty signing key is required.")
    if not run_uuid or not run_uuid.strip():
        raise ValueError("A non-empty run uuid is required.")

    return hmac.new(
        signing_key.encode(),
        DERIVATION_PREFIX + run_uuid.encode(),
        hashlib.sha256,
    ).hexdigest()


def derive_sandbox_token_from_env(run_uuid: str) -> str:
    signing_key = os.environ.get(ENV_KEYS_SECRET_INTERNAL_TOKEN)
    if not signing_key or not signing_key.strip():
        raise PolyaxonConverterError(
            "plugins.sandbox is enabled but "
            f"{ENV_KEYS_SECRET_INTERNAL_TOKEN} is not set."
        )
    return derive_sandbox_token(signing_key, run_uuid)
