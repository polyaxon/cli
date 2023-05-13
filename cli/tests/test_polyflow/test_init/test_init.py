import pytest

from pydantic import ValidationError

from polyaxon.polyflow import V1Init, V1RunKind
from polyaxon.polyflow.operations import V1CompiledOperation
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.init_mark
class TestInit(BaseTestCase):
    def test_op_with_init(self):
        config_dict = {
            "kind": "compiled_operation",
            "run": {
                "kind": V1RunKind.JOB,
                "container": {"image": "foo/bar"},
                "init": [
                    {"container": {"name": "init1", "args": ["/subpath1", "subpath2"]}},
                    {
                        "connection": "s3",
                        "container": {
                            "name": "init2",
                            "args": ["/subpath1", "subpath2"],
                        },
                    },
                    {"connection": "repo3", "git": {"revision": "foo"}},
                    {"file": {"filename": "test", "content": "test"}},
                ],
            },
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

    def test_init_config(self):
        config_dict = {
            "container": {"name": "init1", "args": ["/subpath1", "subpath2"]}
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {"connection": "foo"}
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "connection": "foo",
            "container": {"name": "init1", "args": ["/subpath1", "subpath2"]},
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "connection": "foo",
            "git": {"revision": "branch1"},
            "container": {"name": "init1", "args": ["/subpath1", "subpath2"]},
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "connection": "foo",
            "artifacts": {"files": ["path1", "path2"]},
            "container": {"name": "init1", "args": ["/subpath1", "subpath2"]},
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "connection": "foo",
            "paths": ["path1", "path2"],
            "container": {"name": "init1", "args": ["/subpath1", "subpath2"]},
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "dockerfile": {
                "image": "tensorflow:1.3.0",
                "path": ["./module"],
                "copy": ["/foo/bar"],
                "run": ["pip install tensor2tensor"],
                "env": {"LC_ALL": "en_US.UTF-8"},
                "filename": "dockerfile",
                "workdir": "",
                "shell": "sh",
            }
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            "file": {
                "filename": "dockerfile",
                "content": "test",
                "chmod": "+x",
            }
        }
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        # artifacts without connection
        config_dict = {"artifacts": {"files": ["path1", "path2"]}}
        config = V1Init.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

    def test_wrong_init_configs(self):
        # Git without url and connection
        config_dict = {
            "git": {"revision": "branch1"},
            "container": {"name": "init1", "args": ["/subpath1", "subpath2"]},
        }
        with self.assertRaises(ValidationError):
            V1Init.from_dict(config_dict)

        # artifacts without connection
        config_dict = {
            "git": {"revision": "branch1"},
            "artifacts": {"files": ["path1", "path2"]},
        }
        with self.assertRaises(ValidationError):
            V1Init.from_dict(config_dict)

        # both git and dockerfile at the same time
        config_dict = {
            "git": {"revision": "branch1"},
            "dockerfile": {"image": "tensorflow:1.3.0"},
        }
        with self.assertRaises(ValidationError):
            V1Init.from_dict(config_dict)
