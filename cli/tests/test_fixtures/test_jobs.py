import pytest

from polyaxon._flow import V1Operation
from polyaxon._utils.fixtures import (
    get_fxt_job,
    get_fxt_job_with_inputs,
    get_fxt_job_with_inputs_and_conditions,
    get_fxt_job_with_inputs_and_joins,
    get_fxt_job_with_inputs_outputs,
    get_fxt_ray_cluster,
    get_fxt_tf_job,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestJobsFixtures(BaseTestCase):
    def test_fxt_job(self):
        config = get_fxt_job()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_job_with_inputs(self):
        config = get_fxt_job_with_inputs()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_job_with_inputs_outputs(self):
        config = get_fxt_job_with_inputs_outputs()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_job_with_inputs_and_conditions(self):
        config = get_fxt_job_with_inputs_and_conditions()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_job_with_inputs_and_joins(self):
        config = get_fxt_job_with_inputs_and_joins()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_tf_job(self):
        config = get_fxt_tf_job()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_ray_cluster(self):
        config = get_fxt_ray_cluster()
        assert V1Operation.read(config).to_dict() == config
