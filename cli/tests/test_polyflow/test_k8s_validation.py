import pytest

from clipped.compact.pydantic import ValidationError
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.init import V1Init
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.dask.replica import V1DaskReplica
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.ray.replica import V1RayReplica
from polyaxon._flow.run.service import V1Service
from polyaxon._utils.test_utils import BaseTestCase


RUNTIME_MODELS = (V1Job, V1Service, V1KFReplica, V1DaskReplica, V1RayReplica)


@pytest.mark.polyflow_mark
class TestK8sFieldValidation(BaseTestCase):
    def test_kubernetes_lists_validate_shapes_and_elements(self):
        for model, field, item in (
            (V1Job, "sidecars", {"name": "helper", "image": "busybox:1.37"}),
            (V1Job, "volumes", {"name": "scratch", "emptyDir": {}}),
            (V1KFReplica, "sidecars", {"name": "helper", "image": "busybox:1.37"}),
            (V1Dag, "volumes", {"name": "scratch", "emptyDir": {}}),
            (
                V1Environment,
                "tolerations",
                {"key": "workload", "operator": "Exists"},
            ),
        ):
            for value in (None, []):
                with self.subTest(model=model.__name__, field=field, value=value):
                    assert getattr(model(**{field: value}), field) == value

            with self.subTest(model=model.__name__, field=field, value=[item]):
                assert model(**{field: [item]}).to_dict()[field] == [item]

            for value in (True, 1, False, 0, "{{ s }}", ["{{ s }}"]):
                with (
                    self.subTest(model=model.__name__, field=field, value=value),
                    self.assertRaisesRegex(ValidationError, field),
                ):
                    model(**{field: value})

    def test_kubernetes_fields_reject_scalars_and_whole_field_references(self):
        cases = [
            (model, field)
            for model in RUNTIME_MODELS
            for field in ("sidecars", "volumes")
        ]
        cases += [
            (V1Dag, "volumes"),
            (V1Environment, "tolerations"),
            (V1Environment, "host_aliases"),
        ]
        for model, field in cases:
            for value in (True, 1, "{{ s }}"):
                with (
                    self.subTest(model=model.__name__, field=field, value=value),
                    self.assertRaises(ValidationError),
                ):
                    model(**{field: value})
        for model in (*RUNTIME_MODELS, V1Init):
            with (
                self.subTest(model=model.__name__, field="container"),
                self.assertRaises(ValidationError),
            ):
                model(container="{{ c }}")
