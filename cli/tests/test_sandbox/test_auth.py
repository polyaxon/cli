import hashlib
import hmac
import os
import uuid

from unittest import TestCase

import pytest

from polyaxon._env_vars.keys import ENV_KEYS_SECRET_INTERNAL_TOKEN
from polyaxon._sandbox.auth import (
    DERIVATION_PREFIX,
    derive_sandbox_token,
    derive_sandbox_token_from_env,
)
from polyaxon.exceptions import PolyaxonConverterError


@pytest.mark.utils_mark
class TestSandboxAuth(TestCase):
    def setUp(self):
        super().setUp()
        self.current_internal_token = os.environ.get(ENV_KEYS_SECRET_INTERNAL_TOKEN)

    def tearDown(self):
        if self.current_internal_token is None:
            os.environ.pop(ENV_KEYS_SECRET_INTERNAL_TOKEN, None)
        else:
            os.environ[ENV_KEYS_SECRET_INTERNAL_TOKEN] = self.current_internal_token
        super().tearDown()

    def test_derive_sandbox_token(self):
        signing_key = "internal-token"
        run_uuid = uuid.uuid4().hex
        expected = hmac.new(
            signing_key.encode(),
            DERIVATION_PREFIX + run_uuid.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert derive_sandbox_token(signing_key, run_uuid) == expected

    def test_derive_sandbox_token_scopes_by_key_and_run_uuid(self):
        run_uuid = uuid.uuid4().hex
        token = derive_sandbox_token("internal-token", run_uuid)

        assert token != derive_sandbox_token("other-token", run_uuid)
        assert token != derive_sandbox_token("internal-token", uuid.uuid4().hex)

    def test_derive_sandbox_token_rejects_empty_inputs(self):
        with self.assertRaises(ValueError):
            derive_sandbox_token("", uuid.uuid4().hex)

        with self.assertRaises(ValueError):
            derive_sandbox_token("internal-token", "")

    def test_derive_sandbox_token_from_env(self):
        os.environ[ENV_KEYS_SECRET_INTERNAL_TOKEN] = "internal-token"
        run_uuid = uuid.uuid4().hex

        assert derive_sandbox_token_from_env(run_uuid) == derive_sandbox_token(
            "internal-token", run_uuid
        )

    def test_derive_sandbox_token_from_env_requires_internal_token(self):
        os.environ.pop(ENV_KEYS_SECRET_INTERNAL_TOKEN, None)

        with self.assertRaises(PolyaxonConverterError) as ctx:
            derive_sandbox_token_from_env(uuid.uuid4().hex)
        assert ENV_KEYS_SECRET_INTERNAL_TOKEN in str(ctx.exception)
