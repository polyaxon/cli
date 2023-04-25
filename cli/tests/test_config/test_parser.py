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

import uuid

from clipped.config.constants import NO_VALUE_FOUND

from polyaxon.config.parser import ConfigParser
from polyaxon.exceptions import PolyaxonSchemaError
from polyaxon.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1GitType,
    V1TensorboardType,
)
from polyaxon.utils.test_utils import BaseTestCase


class TestConfigParser(BaseTestCase):
    def test_get_dockerfile_init(self):
        get_dockerfile_init = ConfigParser.parse(V1DockerfileType)
        value = get_dockerfile_init(
            key="dict_key_1", value={"image": "foo", "env": {"key1": 2, "key2": 21}}
        )
        self.assertEqual(
            value, V1DockerfileType(image="foo", env={"key1": 2, "key2": 21})
        )

        value = get_dockerfile_init(
            key="dict_key_1", value='{"image": "foo", "env": {"key1": 2, "key2": 21}}'
        )
        self.assertEqual(
            value, V1DockerfileType(image="foo", env={"key1": 2, "key2": 21})
        )

        value = get_dockerfile_init(
            key="dict_key_1", value='{"image": "foo", "run": ["exec1", "exec2"]}'
        )
        self.assertEqual(value, V1DockerfileType(image="foo", run=["exec1", "exec2"]))

        value = get_dockerfile_init(
            key="dict_list_key_1",
            value=[
                {"image": "foo", "env": {"key1": 2, "key2": 21}},
                {"image": "foo2", "copy": ["exec1", "exec2"]},
                {"image": "foo3", "run": ["exec1", "exec2"]},
            ],
            is_list=True,
        )
        self.assertEqual(
            value,
            [
                V1DockerfileType(image="foo", env={"key1": 2, "key2": 21}),
                V1DockerfileType(image="foo2", copy_=["exec1", "exec2"]),
                V1DockerfileType(image="foo3", run=["exec1", "exec2"]),
            ],
        )

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_error_key_1", value=None)

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_error_key_1", value="foo")

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_error_key_2", value=1)

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_error_key_3", value=False)

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_error_key_4", value=["1", "foo"])

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_list_key_1", value=["123", {"key3": True}])

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(
                key="dict_list_error_key_1", value=["123", {"key3": True}], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(
                key="dict_list_error_key_2", value=[{"key3": True}, 12.3], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(
                key="dict_list_error_key_3", value=[{"key3": True}, None], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(
                key="dict_list_error_key_4",
                value=[{"key3": True}, "123", False],
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(
                key="dict_key_1",
                value={"key1": "foo", "key2": 2, "key3": False, "key4": "1"},
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_non_existing_key", value=None)

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_non_existing_key", value=NO_VALUE_FOUND)

        with self.assertRaises(PolyaxonSchemaError):
            get_dockerfile_init(key="dict_non_existing_key", value=None, is_list=True)

        self.assertEqual(
            get_dockerfile_init(
                key="dict_non_existing_key", value=None, is_optional=True
            ),
            None,
        )

    def test_get_file_init(self):
        get_file_init = ConfigParser.parse(V1FileType)
        value = get_file_init(
            key="dict_key_1", value={"filename": "foo.yaml", "content": "test"}
        )
        self.assertEqual(value, V1FileType(filename="foo.yaml", content="test"))

        value = get_file_init(key="dict_key_1", value={"content": "test"})
        self.assertEqual(value, V1FileType(content="test"))

        value = get_file_init(
            key="dict_key_1", value='{"filename": "foo.yaml", "content": "test"}'
        )
        self.assertEqual(value, V1FileType(filename="foo.yaml", content="test"))

        value = get_file_init(key="dict_key_1", value='{"content": "test"}')
        self.assertEqual(value, V1FileType(content="test"))

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_error_key_1",
                value=dict(content="foo", connection="foo", init=True),
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_error_key_1", value=dict(content="foo", init=True))

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_error_key_1", value=dict(content="foo", connection="foo")
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_error_key_1", value="foo")

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_error_key_2", value=1)

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_error_key_3", value=False)

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_error_key_4", value=["1", "foo"])

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_list_key_1", value=["123", {"key3": True}])

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_list_error_key_1", value=["123", {"key3": True}], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_list_error_key_2", value=[{"key3": True}, 12.3], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_list_error_key_3", value=[{"key3": True}, None], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_list_error_key_4",
                value=[{"key3": True}, "123", False],
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(
                key="dict_key_1",
                value={"key1": "foo", "key2": 2, "key3": False, "key4": "1"},
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_non_existing_key", value=None)

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_non_existing_key", value=NO_VALUE_FOUND)

        with self.assertRaises(PolyaxonSchemaError):
            get_file_init(key="dict_non_existing_key", value=None, is_list=True)

        self.assertEqual(
            get_file_init(key="dict_non_existing_key", value=None, is_optional=True),
            None,
        )

    def test_get_git_init(self):
        get_git_init = ConfigParser.parse(V1GitType)
        value = get_git_init(key="dict_key_1", value={"revision": "foo"})
        self.assertEqual(value, V1GitType(revision="foo"))

        value = get_git_init(
            key="dict_key_1",
            value={"revision": "foo"},
        )
        self.assertEqual(value, V1GitType(revision="foo"))

        value = get_git_init(
            key="dict_key_1", value={"url": "https://github.com", "revision": "foo"}
        )
        self.assertEqual(value, V1GitType(revision="foo", url="https://github.com"))

        value = get_git_init(
            key="dict_key_1", value='{"revision": "foo", "url": "https://github.com"}'
        )
        self.assertEqual(value, V1GitType(revision="foo", url="https://github.com"))

        value = get_git_init(key="dict_key_1", value='{"revision": "foo"}')
        self.assertEqual(value, V1GitType(revision="foo"))

        value = get_git_init(
            key="dict_list_key_1",
            value=[
                {"revision": "foo"},
                {"url": "https://github.com", "revision": "foo"},
                {"url": "https://github.com"},
            ],
            is_list=True,
        )
        self.assertEqual(
            value,
            [
                V1GitType(revision="foo"),
                V1GitType(revision="foo", url="https://github.com"),
                V1GitType(url="https://github.com"),
            ],
        )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_error_key_1",
                value=dict(revision="foo", connection="foo", init=True),
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_error_key_1", value=dict(revision="foo", init=True))

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_error_key_1", value=dict(revision="foo", connection="foo")
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_error_key_1", value="foo")

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_error_key_2", value=1)

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_error_key_3", value=False)

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_error_key_4", value=["1", "foo"])

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_list_key_1", value=["123", {"key3": True}])

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_list_error_key_1", value=["123", {"key3": True}], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_list_error_key_2", value=[{"key3": True}, 12.3], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_list_error_key_3", value=[{"key3": True}, None], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_list_error_key_4",
                value=[{"key3": True}, "123", False],
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(
                key="dict_key_1",
                value={"key1": "foo", "key2": 2, "key3": False, "key4": "1"},
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_non_existing_key", value=None)

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_non_existing_key", value=NO_VALUE_FOUND)

        with self.assertRaises(PolyaxonSchemaError):
            get_git_init(key="dict_non_existing_key", value=None, is_list=True)

        self.assertEqual(
            get_git_init(key="dict_non_existing_key", value=None, is_optional=True),
            None,
        )

    def test_get_tensorboard_init(self):
        get_tensorboard_init = ConfigParser.parse(V1TensorboardType)
        value = get_tensorboard_init(key="dict_key_1", value={"port": 8000})
        self.assertEqual(value, V1TensorboardType(port=8000))

        value = get_tensorboard_init(
            key="dict_key_1",
            value={"port": 8000},
        )
        self.assertEqual(value, V1TensorboardType(port=8000))

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_key_1", value={"port": 8000, "uuids": "uuid1, uuid2"}
            )

        uuids = "{},{}".format(uuid.uuid4().hex, uuid.uuid4().hex)
        value = get_tensorboard_init(
            key="dict_key_1", value={"port": 8000, "uuids": uuids}
        )
        self.assertEqual(value, V1TensorboardType(port=8000, uuids=uuids))

        uuids = [uuid.uuid4(), uuid.uuid4().hex]
        value = get_tensorboard_init(
            key="dict_key_1", value={"port": 8000, "uuids": uuids}
        )
        self.assertEqual(value, V1TensorboardType(port=8000, uuids=uuids))

        uuids = [uuid.uuid4().hex, uuid.uuid4().hex]
        value = get_tensorboard_init(
            key="dict_key_1",
            value='{{"port": 8000, "uuids": ["{}","{}"]}}'.format(*uuids),
        )
        self.assertEqual(value, V1TensorboardType(port=8000, uuids=uuids))

        value = get_tensorboard_init(key="dict_key_1", value='{"useNames": false}')
        self.assertEqual(value, V1TensorboardType(use_names=False))

        value = get_tensorboard_init(
            key="dict_list_key_1",
            value=[
                {"useNames": False},
                {"uuids": uuids},
                {
                    "port": 8000,
                    "uuids": uuids,
                    "plugins": ["plug1", "plug2"],
                },
            ],
            is_list=True,
        )
        self.assertEqual(
            value,
            [
                V1TensorboardType(use_names=False),
                V1TensorboardType(uuids=uuids),
                V1TensorboardType(port=8000, uuids=uuids, plugins=["plug1", "plug2"]),
            ],
        )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_error_key_1",
                value=dict(port="foo"),
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_error_key_1", value=dict(port=8000, init=True)
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_error_key_1", value=dict(port=8000, connection="foo")
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_error_key_1", value="foo")

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_error_key_2", value=1)

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_error_key_3", value=False)

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_error_key_4", value=["1", "foo"])

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_list_key_1", value=["123", {"key3": True}])

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_list_error_key_1", value=["123", {"key3": True}], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_list_error_key_2", value=[{"key3": True}, 12.3], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_list_error_key_3", value=[{"key3": True}, None], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_list_error_key_4",
                value=[{"key3": True}, "123", False],
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(
                key="dict_key_1",
                value={"key1": "foo", "key2": 2, "key3": False, "key4": "1"},
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_non_existing_key", value=None)

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_non_existing_key", value=NO_VALUE_FOUND)

        with self.assertRaises(PolyaxonSchemaError):
            get_tensorboard_init(key="dict_non_existing_key", value=None, is_list=True)

        self.assertEqual(
            get_tensorboard_init(
                key="dict_non_existing_key", value=None, is_optional=True
            ),
            None,
        )

    def test_get_artifacts_init(self):
        get_artifacts_init = ConfigParser.parse(V1ArtifactsType)
        value = get_artifacts_init(key="dict_key_1", value={"files": ["foo", "bar"]})
        self.assertEqual(value, V1ArtifactsType(files=["foo", "bar"]))

        value = get_artifacts_init(
            key="dict_key_1", value={"files": [["from-foo", "to-foo"], "bar"]}
        )
        self.assertEqual(value, V1ArtifactsType(files=[["from-foo", "to-foo"], "bar"]))

        value = get_artifacts_init(key="dict_key_1", value='{"dirs": ["foo", "bar"]}')
        self.assertEqual(value, V1ArtifactsType(dirs=["foo", "bar"]))

        value = get_artifacts_init(
            key="dict_key_1", value='{"dirs": [["from-foo", "to-foo"], "bar"]}'
        )
        self.assertEqual(value, V1ArtifactsType(dirs=[["from-foo", "to-foo"], "bar"]))

        value = get_artifacts_init(
            key="dict_list_key_1",
            value=[
                {
                    "dirs": [["from-foo", "to-foo"], "bar"],
                    "files": [["from-foo", "to-foo"], "bar"],
                },
                {"files": [["from-foo", "to-foo"], "bar"]},
            ],
            is_list=True,
        )
        self.assertEqual(
            value,
            [
                V1ArtifactsType(
                    dirs=[["from-foo", "to-foo"], "bar"],
                    files=[["from-foo", "to-foo"], "bar"],
                ),
                V1ArtifactsType(files=[["from-foo", "to-foo"], "bar"]),
            ],
        )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_key_1", value={"connection": "foo", "init": True}
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_key_1", value={"init": True, "dirs": ["foo", "bar"]}
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_key_1", value={"connection": "foo", "files": ["foo", "bar"]}
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_error_key_1", value={"paths": ["foo", "bar"]})

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_error_key_1", value="foo")

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_error_key_2", value=1)

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_error_key_3", value=False)

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_error_key_4", value=["1", "foo"])

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_list_key_1", value=["123", {"key3": True}])

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_list_error_key_1", value=["123", {"key3": True}], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_list_error_key_2", value=[{"key3": True}, 12.3], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_list_error_key_3", value=[{"key3": True}, None], is_list=True
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_list_error_key_4",
                value=[{"key3": True}, "123", False],
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(
                key="dict_key_1",
                value={"key1": "foo", "key2": 2, "key3": False, "key4": "1"},
                is_list=True,
            )

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_non_existing_key", value=None)

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_non_existing_key", value=NO_VALUE_FOUND)

        with self.assertRaises(PolyaxonSchemaError):
            get_artifacts_init(key="dict_non_existing_key", value=None, is_list=True)

        self.assertEqual(
            get_artifacts_init(
                key="dict_non_existing_key", value=None, is_optional=True
            ),
            None,
        )
