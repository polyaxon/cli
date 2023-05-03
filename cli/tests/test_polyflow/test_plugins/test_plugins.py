#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from clipped.utils.assertions import assert_equal_dict

from polyaxon.polyaxonfile.specs import kinds
from polyaxon.polyflow import V1CompiledOperation, V1RunKind
from polyaxon.polyflow.plugins import V1Plugins
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.plugins_mark
class TestPluginsConfigs(BaseTestCase):
    def test_plugins_config(self):
        # Add auth
        config_dict = {"auth": True}

        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add docker
        config_dict["docker"] = True
        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add shm
        config_dict["shm"] = True
        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add outputs
        config_dict["collectArtifacts"] = True
        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add logs
        config_dict["collectLogs"] = True
        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add resources
        config_dict["collectResources"] = True
        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add notifications
        config_dict["notifications"] = [
            {"connections": ["test1"], "trigger": "succeeded"},
            {"connections": ["test2"], "trigger": "failed"},
            {"connections": ["test3"], "trigger": "done"},
        ]
        config = V1Plugins.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

    def test_get_from_spec(self):
        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "mountArtifactsStore": False,
                    "collectLogs": False,
                    "collectArtifacts": False,
                    "syncStatuses": False,
                    "externalHost": True,
                },
                "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}},
            }
        )
        plugins = compiled_operation.plugins
        plugins = V1Plugins.get_or_create(plugins)
        assert plugins.auth is False
        assert plugins.docker is False
        assert plugins.shm is False
        assert plugins.mount_artifacts_store is False
        assert plugins.collect_artifacts is False
        assert plugins.collect_logs is False
        assert plugins.sync_statuses is False
        assert plugins.external_host is True

    def test_get_from_env(self):
        spec = V1Plugins(
            auth=True,
            shm=True,
            docker=True,
            mount_artifacts_store=True,
            collect_artifacts=True,
            collect_logs=True,
            sync_statuses=True,
            external_host=True,
        )
        spec = V1Plugins.get_or_create(spec)
        assert spec.auth is True
        assert spec.docker is True
        assert spec.shm is True
        assert spec.mount_artifacts_store is True
        assert spec.collect_artifacts is True
        assert spec.collect_logs is True
        assert spec.sync_statuses is True
        assert spec.external_host is True

    def test_get_from_empty_env(self):
        spec = V1Plugins()
        spec = V1Plugins.get_or_create(spec, auth=True)
        assert spec.auth is True
        assert spec.docker is False
        assert spec.shm is True
        assert spec.mount_artifacts_store is False
        assert spec.collect_artifacts is True
        assert spec.collect_logs is True
        assert spec.sync_statuses is True
        assert spec.external_host is False

        spec = V1Plugins()
        spec = V1Plugins.get_or_create(spec)
        assert spec.auth is False
        assert spec.docker is False
        assert spec.shm is True
        assert spec.mount_artifacts_store is False
        assert spec.collect_artifacts is True
        assert spec.collect_logs is True
        assert spec.sync_statuses is True
        assert spec.external_host is False
