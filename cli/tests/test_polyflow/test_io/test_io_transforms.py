import pytest
import uuid

from collections import OrderedDict

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict
from clipped.utils.json import orjson_dumps

from polyaxon import types
from polyaxon._flow.io import V1IO
from polyaxon._flow.params import ParamSpec, V1Param
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonValidationError


@pytest.mark.polyflow_mark
class TestV1IOTransforms(BaseTestCase):
    def test_get_param(self):
        # None string values should exit fast
        param = V1Param(value=1)
        assert param.get_spec(
            name="foo",
            iotype="int",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="int",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        # Str values none regex
        param = V1Param(value="1")
        assert param.get_spec(
            name="foo",
            iotype="int",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="int",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        param = V1Param(value="SDfd")
        assert param.get_spec(
            name="foo",
            iotype="str",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        # Validation dag
        param = V1Param(value="inputs.foo", ref="dag")
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        param = V1Param(value="{{ inputs }}", ref="dag")
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        with self.assertRaises(PolyaxonValidationError):
            param = V1Param(value="{{ outputs }}", ref="dag")
            param.get_spec(
                name="foo",
                iotype="bool",
                is_flag=True,
                is_list=False,
                is_context=False,
                arg_format=None,
            )

        with self.assertRaises(PolyaxonValidationError):
            param = V1Param(value="inputs.foo", ref="dag.1")
            param.get_spec(
                name="foo",
                iotype="bool",
                is_flag=True,
                is_list=False,
                is_context=False,
                arg_format=None,
            )

        # Validation ops
        param = V1Param(value="{{ outputs.foo }}", ref="ops.foo-bar")
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        param = V1Param(value="inputs.foo", ref="ops.foo-bar")
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        param = V1Param(value="inputs", ref="ops.foo-bar")
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        # Regex validation ops: invalid params
        with self.assertRaises(PolyaxonValidationError):
            param = V1Param(value="status.foo", ref="ops.foo-bar")
            param.get_spec(
                name="foo",
                iotype="bool",
                is_flag=True,
                is_list=False,
                is_context=False,
                arg_format=None,
            )

        # Validation runs
        uid = uuid.uuid4().hex
        param = V1Param(value="outputs.foo", ref="runs.{}".format(uid))
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        uid = uuid.uuid4().hex
        param = V1Param(value="inputs.foo", ref="runs.{}".format(uid))
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format=None,
        )

        # Custom arg_format
        param = V1Param(value="SDfd")
        assert param.get_spec(
            name="foo",
            iotype="str",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format="--sdf={{ foo }}",
        ) == ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="--sdf={{ foo }}",
        )
        assert (
            ParamSpec(
                name="foo",
                type="str",
                param=param,
                is_flag=False,
                is_list=False,
                is_context=False,
                is_requested=True,
                arg_format="--sdf={{ foo }}",
            ).as_arg()
            == "--sdf=SDfd"
        )

        # Custom arg_format with empty value
        param = V1Param(value=None)
        assert param.get_spec(
            name="foo",
            iotype="str",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format="--sdf={{ foo }}",
        ) == ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="--sdf={{ foo }}",
        )
        assert (
            ParamSpec(
                name="foo",
                type="str",
                param=param,
                is_flag=False,
                is_list=False,
                is_context=False,
                is_requested=True,
                arg_format="--sdf={{ foo }}",
            ).as_arg()
            == ""
        )

        # Custom arg_format with 0 value
        param = V1Param(value=0)
        assert param.get_spec(
            name="foo",
            iotype="int",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format="--sdf={{ foo }}",
        ) == ParamSpec(
            name="foo",
            type="int",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="--sdf={{ foo }}",
        )
        assert (
            ParamSpec(
                name="foo",
                type="int",
                param=param,
                is_flag=False,
                is_list=False,
                is_context=False,
                is_requested=True,
                arg_format="--sdf={{ foo }}",
            ).as_arg()
            == "--sdf=0"
        )

        # Custom arg_format with bool value
        param = V1Param(value=True)
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format="{{'true-var' if foo else 'false-var'}}",
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="{{'true-var' if foo else 'false-var'}}",
        )
        assert (
            ParamSpec(
                name="foo",
                type="bool",
                param=param,
                is_flag=False,
                is_list=False,
                is_context=False,
                is_requested=True,
                arg_format="{{'true-var' if foo else 'false-var'}}",
            ).as_arg()
            == "true-var"
        )

        param = V1Param(value=False)
        assert param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format="{{'true-var' if foo else 'false-var'}}",
        ) == ParamSpec(
            name="foo",
            type="bool",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="{{'true-var' if foo else 'false-var'}}",
        )
        assert (
            ParamSpec(
                name="foo",
                type="bool",
                param=param,
                is_flag=False,
                is_list=False,
                is_context=False,
                is_requested=True,
                arg_format="{{'true-var' if foo else 'false-var'}}",
            ).as_arg()
            == "false-var"
        )

        # isFlag
        param = V1Param(value=True)
        assert param.get_spec(
            name="foo",
            iotype="str",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format="{{foo}}",
        ) == ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="{{foo}}",
        )
        assert (
            str(
                ParamSpec(
                    name="foo",
                    type="str",
                    param=param,
                    is_flag=True,
                    is_list=False,
                    is_context=False,
                    is_requested=True,
                    arg_format="{{foo}}",
                )
            )
            == "--foo"
        )

        # isFlag empty
        param = V1Param(value=None)
        assert param.get_spec(
            name="foo",
            iotype="str",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format="{{foo}}",
        ) == ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=True,
            is_list=False,
            is_context=False,
            is_requested=True,
            arg_format="{{foo}}",
        )
        assert (
            str(
                ParamSpec(
                    name="foo",
                    type="str",
                    param=param,
                    is_flag=True,
                    is_list=False,
                    is_context=False,
                    is_requested=True,
                    arg_format="{{foo}}",
                )
            )
            == ""
        )

        # isContext
        param = V1Param(value={"key": "value"})
        assert param.get_spec(
            name="foo",
            iotype="str",
            is_flag=False,
            is_list=False,
            is_context=True,
            arg_format="{{foo}}",
        ) == ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=True,
            is_requested=True,
            arg_format="{{foo}}",
        )
        assert ParamSpec(
            name="foo",
            type="str",
            param=param,
            is_flag=False,
            is_list=False,
            is_context=True,
            is_requested=True,
            arg_format=None,
        ).param.value == {"key": "value"}
        assert str(
            ParamSpec(
                name="foo",
                type="str",
                param=param,
                is_flag=False,
                is_list=False,
                is_context=True,
                is_requested=True,
                arg_format=None,
            )
        ) == orjson_dumps({"key": "value"})

        # Regex validation runs: invalid params
        with self.assertRaises(PolyaxonValidationError):
            param = V1Param(value="outputs.foo", ref="run.foo-bar")
            param.get_spec(
                name="foo",
                iotype="bool",
                is_flag=True,
                is_list=False,
                is_context=False,
                arg_format=None,
            )

    def test_validate_to_init(self):
        param = V1Param(value="test")
        spec = param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.validate_to_init() is False

        # Add connection
        spec.param.connection = "connection"
        assert spec.validate_to_init() is False

        # Add to_init
        spec.param.to_init = True
        assert spec.validate_to_init() is True

        # Dockerfile but no to_init
        param = V1Param(value="test")
        spec = param.get_spec(
            name="foo",
            iotype=types.DOCKERFILE,
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.validate_to_init() is False

        # add to_init
        spec.param.to_init = True
        assert spec.validate_to_init() is True

        # Add connection
        spec.param.connection = "test"
        assert spec.validate_to_init() is True

    def test_to_init(self):
        param = V1Param(value="test", connection="connection")
        spec = param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.to_init() is None

        param = V1Param(value="test", to_init=True)
        spec = param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.to_init() is None

        param = V1Param(value="test", connection="connection", to_init=True)
        spec = param.get_spec(
            name="foo",
            iotype="bool",
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        init = spec.to_init()
        assert init.container is None
        assert init.connection == "connection"
        assert init.dockerfile is None
        assert init.git is None
        assert init.artifacts is None

        # Dockerfile
        param = V1Param(value={"image": "test"}, connection="connection")
        spec = param.get_spec(
            name="foo",
            iotype=types.DOCKERFILE,
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.to_init() is None

        param = V1Param(value={"image": "test"}, to_init=True)
        spec = param.get_spec(
            name="foo",
            iotype=types.DOCKERFILE,
            is_flag=True,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        init = spec.to_init()
        assert init.container is None
        assert init.connection is None
        assert init.dockerfile.image == param.value["image"]
        assert init.git is None
        assert init.artifacts is None

        # Git
        param = V1Param(value={"url": "test"}, connection="connection")
        spec = param.get_spec(
            name="foo",
            iotype=types.GIT,
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.to_init() is None

        param = V1Param(value={"url": "test"}, connection="connection", to_init=True)
        spec = param.get_spec(
            name="foo",
            iotype=types.GIT,
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        init = spec.to_init()
        assert init.container is None
        assert init.connection == "connection"
        assert init.dockerfile is None
        assert init.git.to_dict() == param.value
        assert init.artifacts is None

        # Artifacts
        param = V1Param(value={"files": ["test"]}, connection="connection")
        spec = param.get_spec(
            name="foo",
            iotype=types.ARTIFACTS,
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        assert spec.to_init() is None

        param = V1Param(
            value={"files": ["test"]}, connection="connection", to_init=True
        )
        spec = param.get_spec(
            name="foo",
            iotype=types.ARTIFACTS,
            is_flag=False,
            is_list=False,
            is_context=False,
            arg_format=None,
        )
        init = spec.to_init()
        assert init.container is None
        assert init.connection == "connection"
        assert init.dockerfile is None
        assert init.git is None
        assert init.artifacts.to_dict() == param.value
