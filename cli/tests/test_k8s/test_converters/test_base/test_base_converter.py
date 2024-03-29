import pytest

from polyaxon._k8s.converter.base import BaseConverter
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonConverterError


@pytest.mark.converter_mark
class TestConverter(BaseTestCase):
    def setUp(self):
        class DummyConverter(BaseConverter):
            SPEC_KIND = "dummy"
            API_VERSION = "v1alpha1"
            PLURAL = "dummies"
            GROUP = "dummy"
            K8S_ANNOTATIONS_KIND = "dummies_name"
            K8S_LABELS_COMPONENT = "dummies_component"
            K8S_LABELS_PART_OF = "dummies_part_of"
            MAIN_CONTAINER_ID = "dummy"

        self.converter = DummyConverter(
            owner_name="foo", project_name="p1", run_name="j1", run_uuid="uuid"
        )
        super().setUp()

    def test_is_valid(self):
        class Converter(BaseConverter):
            pass

        with self.assertRaises(PolyaxonConverterError):
            Converter(
                owner_name="foo", project_name="test", run_name="test", run_uuid="uuid"
            )

    def test_recommended_labels(self):
        assert self.converter.get_recommended_labels(version="v1") == {
            "app.kubernetes.io/name": self.converter.run_name,
            "app.kubernetes.io/instance": self.converter.run_uuid,
            "app.kubernetes.io/version": "v1",
            "app.kubernetes.io/part-of": self.converter.K8S_LABELS_PART_OF,
            "app.kubernetes.io/component": self.converter.K8S_LABELS_COMPONENT,
            "app.kubernetes.io/managed-by": "polyaxon",
        }

    def test_recommended_labels_with_long_name(self):
        self.converter.run_name = "text-sd-bar" * 265
        assert self.converter.get_recommended_labels(version="v1") == {
            "app.kubernetes.io/name": self.converter.run_name[:63],
            "app.kubernetes.io/instance": self.converter.run_uuid,
            "app.kubernetes.io/version": "v1",
            "app.kubernetes.io/part-of": self.converter.K8S_LABELS_PART_OF,
            "app.kubernetes.io/component": self.converter.K8S_LABELS_COMPONENT,
            "app.kubernetes.io/managed-by": "polyaxon",
        }

    def test_run_instance(self):
        assert self.converter.run_instance == "foo.p1.runs.uuid"

    def test_get_labels(self):
        expected = self.converter.get_recommended_labels(version="v1")
        assert self.converter.get_labels(version="v1", labels={}) == expected

        expected = self.converter.get_recommended_labels(version="v1")
        expected.update({"foo": "bar"})
        assert (
            self.converter.get_labels(version="v1", labels={"foo": "bar"}) == expected
        )
