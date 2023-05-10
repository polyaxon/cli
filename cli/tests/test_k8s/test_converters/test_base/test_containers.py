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

from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.base.containers import ContainerMixin
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestSanitizeContainerEnv(BaseTestCase):
    def test_sanitize_container_env_value(self):
        value = [{"foo": "bar"}]
        assert ContainerMixin._sanitize_container_env(value)[0] == {"foo": "bar"}

        value = [{"foo": 1}]
        assert ContainerMixin._sanitize_container_env(value)[0] == {"foo": "1"}

        value = [
            {
                "name": "secret-name",
                "value": True,
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": "true",
        }

        value = [
            {
                "name": "secret-name",
                "value": 1,
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": "1",
        }

        value = [
            {
                "name": "secret-name",
                "value": "test",
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": "test",
        }

        value = [
            {
                "name": "secret-name",
                "value": {"foo": "bar"},
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": '{"foo":"bar"}',
        }

        value = [{"foo": {"key": "value"}}]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "foo": {"key": "value"}
        }

    def test_sanitize_container_env_value_obj(self):
        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value=True,
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value="true",
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value=1,
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value="1",
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value="test",
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value="test",
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value={"foo": "bar"},
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value='{"foo":"bar"}',
        )

    def test_sanitize_container_env_value_from(self):
        value = [
            {
                "name": "secret-name",
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "my-secret",
                        "key": "my-key",
                    }
                },
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "my-secret",
                    "key": "my-key",
                }
            },
        }

        value = [
            {
                "name": "secret-name",
                "valueFrom": {
                    "configKeyRef": {
                        "name": "my-secret",
                        "key": "my-key",
                    }
                },
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "valueFrom": {
                "configKeyRef": {
                    "name": "my-secret",
                    "key": "my-key",
                }
            },
        }

    def test_sanitize_container_env_value_from_obj(self):
        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value_from=k8s_schemas.V1EnvVarSource(
                    config_map_key_ref=k8s_schemas.V1ConfigMapKeySelector(
                        key="my-key",
                        name="my-secret",
                    )
                ),
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value_from=k8s_schemas.V1EnvVarSource(
                config_map_key_ref=k8s_schemas.V1ConfigMapKeySelector(
                    key="my-key",
                    name="my-secret",
                )
            ),
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value_from=k8s_schemas.V1EnvVarSource(
                    config_map_key_ref=k8s_schemas.V1SecretKeySelector(
                        key="my-key",
                        name="my-secret",
                    )
                ),
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value_from=k8s_schemas.V1EnvVarSource(
                config_map_key_ref=k8s_schemas.V1SecretKeySelector(
                    key="my-key",
                    name="my-secret",
                )
            ),
        )
