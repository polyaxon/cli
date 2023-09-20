import numpy as np
import os
import tempfile

from unittest import TestCase, mock

from clipped.utils.json import orjson_dumps
from clipped.utils.paths import delete_path

from polyaxon import _dist, settings
from polyaxon._connections import V1Connection, V1ConnectionKind, V1HostPathConnection
from polyaxon._contexts import paths as ctx_paths
from polyaxon._schemas.agent import AgentConfig
from polyaxon._schemas.authentication import AccessTokenConfig
from polyaxon._schemas.cli import CliConfig
from polyaxon._schemas.client import ClientConfig
from polyaxon.settings import set_agent_config


def assert_equal_feature_processors(fp1, fp2):
    # Check that they have same features
    assert list(fp1.keys()) == list(fp2.key())

    # Check that all features have the same graph
    for feature in fp1:
        assert_equal_graphs(fp2[feature], fp1[feature])


def assert_tensors(tensor1, tensor2):
    if isinstance(tensor1, str):
        tensor1 = [tensor1, 0, 0]

    if isinstance(tensor2, str):
        tensor2 = [tensor2, 0, 0]

    assert tensor1 == tensor2


def assert_equal_graphs(result_graph, expected_graph):
    for i, input_layer in enumerate(expected_graph["input_layers"]):
        assert_tensors(input_layer, result_graph["input_layers"][i])

    for i, output_layer in enumerate(expected_graph["output_layers"]):
        assert_tensors(output_layer, result_graph["output_layers"][i])

    for layer_i, layer in enumerate(result_graph["layers"]):
        layer_name, layer_data = list(layer.items())[0]
        assert layer_name in expected_graph["layers"][layer_i]
        for k, v in layer_data.items():
            assert v == expected_graph["layers"][layer_i][layer_name][k]


def assert_equal_layers(config, expected_layer):
    result_layer = config.to_dict()
    for k, v in expected_layer.items():
        if v is not None or k not in config.REDUCED_ATTRIBUTES:
            assert v == result_layer[k]
        else:
            assert k not in result_layer


def patch_settings(
    set_auth: bool = True,
    set_client: bool = True,
    set_cli: bool = True,
    set_agent: bool = True,
):
    settings.AUTH_CONFIG = None
    if set_auth:
        settings.AUTH_CONFIG = AccessTokenConfig()

    settings.CLIENT_CONFIG = None
    if set_client:
        settings.CLIENT_CONFIG = ClientConfig(host="1.2.3.4")
        settings.CLIENT_CONFIG.tracking_timeout = 0

    settings.CLI_CONFIG = None
    if set_cli:
        settings.CLI_CONFIG = CliConfig(installation={CliConfig._DIST: _dist.EE})

    settings.AGENT_CONFIG = None
    if set_agent:
        set_agent_config(AgentConfig())


class BaseTestCase(TestCase):
    SET_AUTH_SETTINGS = True
    SET_CLIENT_SETTINGS = True
    SET_CLI_SETTINGS = True
    SET_AGENT_SETTINGS = False

    def setUp(self):
        super().setUp()
        delete_path(ctx_paths.CONTEXT_USER_POLYAXON_PATH)
        patch_settings(
            set_auth=self.SET_AUTH_SETTINGS,
            set_client=self.SET_CLIENT_SETTINGS,
            set_cli=self.SET_CLI_SETTINGS,
            set_agent=self.SET_AGENT_SETTINGS,
        )


class TestEnvVarsCase(BaseTestCase):
    @staticmethod
    def check_empty_value(key, expected_function):
        os.environ.pop(key, None)
        assert expected_function() is None

    @staticmethod
    def check_non_dict_value(key, expected_function, value="non dict random value"):
        os.environ[key] = value
        assert expected_function() is None

    @staticmethod
    def check_valid_dict_value(key, expected_function, value):
        os.environ[key] = orjson_dumps(value)
        assert expected_function() == value

    def check_raise_for_invalid_value(self, key, expected_function, value, exception):
        os.environ[key] = orjson_dumps(value)
        with self.assertRaises(exception):
            expected_function()

    @staticmethod
    def check_valid_value(key, expected_function, value, expected_value=None):
        os.environ[key] = value
        expected_value = expected_value or value
        assert expected_function() == expected_value


def tensor_np(shape, dtype=float):
    return np.arange(np.prod(shape), dtype=dtype).reshape(shape)


class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


def set_store():
    store_root = tempfile.mkdtemp()
    config = AgentConfig(
        artifacts_store=V1Connection(
            name="test",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(host_path=store_root, mount_path=store_root),
            secret=None,
        ),
        connections=[],
    )
    set_agent_config(config)
    settings.CLIENT_CONFIG.archives_root = tempfile.mkdtemp()
    return store_root


def create_tmp_files(path):
    for i in range(4):
        open("{}/file{}.txt".format(path, i), "+w")
