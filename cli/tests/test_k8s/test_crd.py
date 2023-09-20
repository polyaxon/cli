from polyaxon._k8s.custom_resources.crd import get_custom_object
from polyaxon._utils.test_utils import BaseTestCase


class TestCRD(BaseTestCase):
    def test_get_custom_object(self):
        crd = get_custom_object(
            namespace="default",
            resource_name="foo",
            kind="job",
            api_version="v1",
            labels={"foo": "bar"},
            annotations={"foo": "bar"},
            custom_object={"some_spec": {"foo": "bar"}},
        )
        assert crd["kind"] == "job"
        assert crd["apiVersion"] == "v1"
        assert crd["metadata"].name == "foo"
        assert crd["metadata"].labels == {"foo": "bar"}
        assert crd["metadata"].annotations == {"foo": "bar"}
        assert crd["metadata"].namespace == "default"
        assert crd["some_spec"] == {"foo": "bar"}
