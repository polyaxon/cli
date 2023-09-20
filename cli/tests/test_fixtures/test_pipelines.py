import pytest

from uuid import uuid4

from polyaxon._flow import V1Operation
from polyaxon._utils.fixtures import (
    get_fxt_build_run_pipeline,
    get_fxt_build_run_pipeline_with_inputs,
    get_fxt_map_reduce,
    get_fxt_pipeline_params_env_termination,
    get_fxt_templated_pipeline_with_upstream_run,
    get_fxt_templated_pipeline_without_params,
    get_fxt_train_tensorboard_events_pipeline,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestPipelinesFixtures(BaseTestCase):
    def test_fxt_templated_pipeline_without_params(self):
        config = get_fxt_templated_pipeline_without_params()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_templated_pipeline_with_upstream_run(self):
        config = get_fxt_templated_pipeline_with_upstream_run(run_uuid=uuid4())
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_build_run_pipeline(self):
        config = get_fxt_build_run_pipeline()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_train_tensorboard_events_pipeline(self):
        config = get_fxt_train_tensorboard_events_pipeline()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_build_run_pipeline_with_inputs(self):
        config = get_fxt_build_run_pipeline_with_inputs()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_pipeline_params_env_termination(self):
        config = get_fxt_pipeline_params_env_termination()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_map_reduce(self):
        config = get_fxt_map_reduce()
        assert V1Operation.read(config).to_dict() == config
