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

from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1HostPathConnection,
    V1K8sResource,
)
from polyaxon.polypod.main.k8s_resources import get_requested_secrets
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.polypod_mark
class TestMainSecrets(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Secrets
        self.resource1 = V1K8sResource(
            name="non_mount_test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        self.resource2 = V1K8sResource(
            name="non_mount_test2",
            is_requested=False,
        )
        self.resource3 = V1K8sResource(
            name="non_mount_test3",
            items=["item1", "item2"],
            is_requested=True,
        )
        self.resource4 = V1K8sResource(
            name="non_mount_test4",
            is_requested=True,
        )
        self.resource5 = V1K8sResource(
            name="non_mount_test1",
            is_requested=True,
        )

        # Connections
        self.s3_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
            secret=self.resource1,
        )
        self.gcs_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gcs//:foo"),
            secret=self.resource2,
        )
        self.az_store = V1Connection(
            name="test_az",
            kind=V1ConnectionKind.WASB,
            schema_=V1BucketConnection(bucket="wasb://x@y.blob.core.windows.net"),
            secret=self.resource3,
        )
        self.claim_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(mount_path="/tmp", volume_claim="test"),
        )
        self.host_path_store = V1Connection(
            name="test_path",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
        )

    def test_get_requested_secrets_non_values(self):
        assert get_requested_secrets(secrets=None, connections=None) == []
        assert get_requested_secrets(secrets=[], connections=[]) == []
        assert (
            get_requested_secrets(
                secrets=[self.resource1, self.resource2], connections=[]
            )
            == []
        )
        assert (
            get_requested_secrets(
                secrets=[], connections=[self.host_path_store, self.claim_store]
            )
            == []
        )

    def test_get_requested_secrets_and_secrets(self):
        expected = get_requested_secrets(secrets=[], connections=[self.s3_store])
        assert expected == [self.resource1]

        expected = get_requested_secrets(
            secrets=[self.resource2], connections=[self.s3_store]
        )
        assert expected == [self.resource1]

        expected = get_requested_secrets(
            secrets=[self.resource2], connections=[self.s3_store, self.gcs_store]
        )
        assert expected == [
            self.resource1,
            self.resource2,
        ]

        expected = get_requested_secrets(
            secrets=[self.resource1, self.resource2],
            connections=[self.s3_store, self.gcs_store, self.az_store],
        )
        assert expected == [
            self.resource1,
            self.resource2,
            self.resource3,
        ]

    def test_get_requested_secrets(self):
        expected = get_requested_secrets(
            secrets=[self.resource1], connections=[self.s3_store]
        )
        assert expected == [self.resource1]
        expected = get_requested_secrets(
            secrets=[self.resource1, self.resource3], connections=[self.s3_store]
        )
        assert expected == [
            self.resource3,
            self.resource1,
        ]
        expected = get_requested_secrets(
            secrets=[self.resource2, self.resource3, self.resource4],
            connections=[self.gcs_store],
        )
        assert expected == [
            self.resource3,
            self.resource4,
            self.resource2,
        ]
        expected = get_requested_secrets(
            secrets=[self.resource1, self.resource2], connections=[self.gcs_store]
        )
        assert expected == [self.resource2]
        expected = get_requested_secrets(
            secrets=[self.resource1, self.resource2],
            connections=[self.s3_store, self.gcs_store],
        )
        assert expected == [
            self.resource1,
            self.resource2,
        ]
        expected = get_requested_secrets(
            secrets=[self.resource1, self.resource2],
            connections=[
                self.s3_store,
                self.gcs_store,
                self.host_path_store,
                self.claim_store,
            ],
        )
        assert expected == [
            self.resource1,
            self.resource2,
        ]

        new_az_store = V1Connection(
            name="test_az",
            kind=V1ConnectionKind.WASB,
            schema_=V1BucketConnection(bucket="wasb://x@y.blob.core.windows.net"),
            secret=self.resource1,
        )
        expected = get_requested_secrets(
            secrets=[self.resource1, self.resource2],
            connections=[
                self.s3_store,
                self.gcs_store,
                new_az_store,
                self.host_path_store,
                self.claim_store,
            ],
        )
        assert expected == [
            self.resource1,
            self.resource2,
        ]

        # Using a requested secret with same id
        expected = get_requested_secrets(
            secrets=[self.resource5, self.resource2],
            connections=[
                self.s3_store,
                self.gcs_store,
                new_az_store,
                self.host_path_store,
                self.claim_store,
            ],
        )
        assert expected == [
            self.resource5,
            self.resource2,
        ]
