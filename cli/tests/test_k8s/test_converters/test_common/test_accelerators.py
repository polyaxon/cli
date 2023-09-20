import pytest

from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.common.accelerators import (
    has_tpu_annotation,
    requests_gpu,
    requests_tpu,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestTPUs(BaseTestCase):
    def test_has_tpu_annotation(self):
        assert has_tpu_annotation(None) is False
        assert has_tpu_annotation({}) is False
        assert has_tpu_annotation({"foo": "bar"}) is False
        assert has_tpu_annotation({"tf-version.cloud-tpus.google.com": "1.13"}) is True

    def test_requests_tpu(self):
        assert (
            requests_tpu(k8s_schemas.V1ResourceRequirements(limits={"cpu": 1})) is False
        )
        assert (
            requests_tpu(
                k8s_schemas.V1ResourceRequirements(
                    limits={"cloud-tpus.google.com/v2": 1}
                )
            )
            is True
        )
        assert (
            requests_tpu(
                k8s_schemas.V1ResourceRequirements(
                    requests={"cloud-tpus.google.com/v2:": 32}
                )
            )
            is True
        )

    def test_requests_gpu(self):
        assert (
            requests_gpu(k8s_schemas.V1ResourceRequirements(limits={"cpu": 1})) is False
        )
        assert (
            requests_gpu(k8s_schemas.V1ResourceRequirements(limits={"amd.com/gpu": 1}))
            is True
        )
        assert (
            requests_gpu(
                k8s_schemas.V1ResourceRequirements(requests={"nvidia.com/gpu": 1})
            )
            is True
        )
