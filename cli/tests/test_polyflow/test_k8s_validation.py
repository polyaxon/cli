import pytest

from clipped.compact.pydantic import ValidationError
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.init import V1Init
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.dask.replica import V1DaskReplica
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.ray.autoscaler import V1RayAutoscalerOptions
from polyaxon._flow.run.ray.replica import V1RayReplica
from polyaxon._flow.run.service import V1Service
from polyaxon._flow.termination import V1ActivityProbe, V1Termination
from polyaxon._schemas.services import BaseServiceConfig
from polyaxon._utils.test_utils import BaseTestCase


RUNTIME_MODELS = (V1Job, V1Service, V1KFReplica, V1DaskReplica, V1RayReplica)


@pytest.mark.polyflow_mark
class TestK8sFieldValidation(BaseTestCase):
    def test_declared_kubernetes_references_survive_validation_and_roundtrip(self):
        cases = [
            (model, ("container", "sidecars", "volumes")) for model in RUNTIME_MODELS
        ]
        cases.extend(
            [
                (V1Dag, ("volumes",)),
                (V1Init, ("container",)),
                (V1RayAutoscalerOptions, ("resources",)),
                (V1Termination, ("pod_failure_policy",)),
            ]
        )
        for model, fields in cases:
            for field in fields:
                with self.subTest(model=model.__name__, field=field):
                    reference = "{{ value }}"

                    config = model(**{field: reference})

                    assert getattr(config, field) == reference
                    restored = model.from_dict(config.to_dict())
                    assert getattr(restored, field) == reference
                    with self.assertRaises(ValidationError):
                        model(**{field: "not-a-reference"})

    def test_kubernetes_lists_validate_shapes_and_elements(self):
        cases = [(model, ("sidecars", "volumes")) for model in RUNTIME_MODELS]
        cases.extend(
            [
                (V1Dag, ("volumes",)),
                (V1Environment, ("tolerations", "host_aliases")),
            ]
        )
        for model, fields in cases:
            for field in fields:
                with self.subTest(model=model.__name__, field=field, value=[]):
                    assert getattr(model(**{field: []}), field) == []
                for value in (True, 1, {"name": "invalid"}, ["{{ value }}"]):
                    with (
                        self.subTest(model=model.__name__, field=field, value=value),
                        self.assertRaises(ValidationError),
                    ):
                        model(**{field: value})

    def test_kubernetes_fields_without_reference_types_reject_strings(self):
        for model, fields in (
            (
                V1Environment,
                (
                    "affinity",
                    "security_context",
                    "dns_config",
                    "tolerations",
                    "host_aliases",
                ),
            ),
            (BaseServiceConfig, ("resources", "affinity", "tolerations")),
            (V1ActivityProbe, ("http", "var_exec")),
        ):
            for field in fields:
                with (
                    self.subTest(model=model.__name__, field=field),
                    self.assertRaises(ValidationError),
                ):
                    model(**{field: "{{ value }}"})
