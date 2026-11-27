import pytest
import subprocess
import sys

from clipped.compact.pydantic import ValidationError
from clipped.config.schema import to_partial
from polyaxon._deploy.schemas.deployment import DeploymentConfig
from polyaxon._deploy.schemas.security_context import SecurityContextConfig
from polyaxon._flow.component import V1Component
from polyaxon._flow.init import V1Init
from polyaxon._flow.io import V1IO
from polyaxon._flow.matrix.bayes import UtilityFunctionConfig
from polyaxon._flow.matrix.params import Range
from polyaxon._flow.operations import V1CompiledOperation, V1Operation
from polyaxon._utils.test_utils import BaseTestCase


JOB = {"kind": "job", "container": {"image": "test"}}
GIT = {"url": "https://github.com/a/b"}

# (model, valid data, invalid data, error fragment, skipped on partial models)
CASES = (
    (
        SecurityContextConfig,
        {"runAsUser": 1, "runAsGroup": 1},
        {"runAsUser": 1},
        "requires both",
        True,
    ),
    (
        DeploymentConfig,
        {},
        {"deploymentChart": "agent", "postgresql": {"enabled": True}},
        "Agent deployment requires",
        False,
    ),
    (
        V1Init,
        {"git": GIT},
        {"git": GIT, "dockerfile": {"image": "test"}},
        "Only one of",
        True,
    ),
    (
        V1IO,
        {"name": "x", "type": "bool", "isFlag": True},
        {"name": "x", "type": "int", "isFlag": True},
        "cannot be a flag",
        True,
    ),
    (
        V1CompiledOperation,
        {"kind": "compiled_operation", "run": JOB},
        {"kind": "compiled_operation", "plugins": {"sandbox": True}, "run": JOB},
        "plugins.sandbox",
        True,
    ),
    (
        Range,
        {"start": 1, "stop": 3, "step": 1},
        {"start": 3, "stop": 1, "step": 1},
        "strictly higher",
        False,
    ),
    (
        UtilityFunctionConfig,
        {"acquisitionFunction": "ucb", "kappa": 1.2},
        {"acquisitionFunction": "ucb"},
        "requires a parameter",
        True,
    ),
    (
        V1Operation,
        {"kind": "operation", "hubRef": "a"},
        {"kind": "operation", "hubRef": "a", "dagRef": "b"},
        "At most one reference",
        True,
    ),
)

MODULES = (
    "polyaxon._deploy.schemas.security_context",
    "polyaxon._deploy.schemas.deployment",
    "polyaxon._flow.init",
    "polyaxon._flow.io.io",
    "polyaxon._flow.operations.compiled_operation",
    "polyaxon._flow.matrix.params",
    "polyaxon._flow.matrix.bayes",
    "polyaxon._flow.polyaxonfile",
)

# Imports the modules in a fresh interpreter, so class creation re-emits warnings.
DEPRECATION_PROBE = """
import importlib, sys, warnings
import pydantic.warnings

category = getattr(pydantic.warnings, "PydanticDeprecatedSince212", None)
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for name in sys.argv[1:]:
        importlib.import_module(name)
for w in caught:
    if category and issubclass(w.category, category) and "model_validator" in str(w.message):
        print(f"{w.filename}:{w.lineno}")
"""


@pytest.mark.schemas_mark
class TestAfterValidators(BaseTestCase):
    def test_full_models_run_after_validators(self):
        for model, valid, invalid, fragment, _ in CASES:
            with self.subTest(model=model.__name__):
                assert isinstance(model.from_dict(valid), model)
                with self.assertRaisesRegex(ValidationError, fragment):
                    model.from_dict(invalid)

    def test_partial_models_skip_after_validators(self):
        for model, _, invalid, _, skipped in CASES:
            if not skipped:
                continue
            with self.subTest(model=model.__name__):
                assert isinstance(to_partial(model).from_dict(invalid), model)

    def test_full_models_validate_partial_instances(self):
        for model, _, invalid, fragment, skipped in CASES:
            if not skipped:
                continue
            with self.subTest(model=model.__name__):
                partial = to_partial(model).from_dict(invalid)
                with self.assertRaisesRegex(ValidationError, fragment):
                    model.model_validate(partial)

    def test_nested_partial_instances_are_validated_as_full(self):
        component = to_partial(V1Component).from_dict(
            {"kind": "component", "hubRef": "a", "dagRef": "b", "run": JOB}
        )
        with self.assertRaisesRegex(ValidationError, "At most one reference"):
            V1Operation.model_validate({"kind": "operation", "component": component})

    def test_no_classmethod_after_validators(self):
        result = subprocess.run(
            [sys.executable, "-c", DEPRECATION_PROBE, *MODULES],
            capture_output=True,
            text=True,
            check=True,
        )
        offenders = [
            line for line in result.stdout.splitlines() if "/polyaxon/" in line
        ]
        assert offenders == []
