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
from typing import Dict, List, Optional, Union

from pydantic import Field, StrictStr

from polyaxon.connections.kinds import V1ConnectionKind
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields.ref_or_obj import RefField


class V1BucketConnection(BaseSchemaModel):
    _IDENTIFIER = "bucket"

    bucket: StrictStr

    def patch(self, schema: "V1BucketConnection"):
        self.bucket = schema.bucket or self.bucket


class V1ClaimConnection(BaseSchemaModel):
    _IDENTIFIER = "volume_claim"

    volume_claim: StrictStr = Field(alias="volumeClaim")
    mount_path: StrictStr = Field(alias="mountPath")
    read_only: Optional[bool] = Field(alias="readOnly")

    def patch(self, schema: "V1ClaimConnection"):
        self.volume_claim = schema.volume_claim or self.volume_claim
        self.mount_path = schema.mount_path or self.mount_path
        self.read_only = schema.read_only or self.read_only


class V1HostPathConnection(BaseSchemaModel):
    _IDENTIFIER = "host_path"

    host_path: StrictStr = Field(alias="hostPath")
    mount_path: StrictStr = Field(alias="mountPath")
    read_only: Optional[bool] = Field(alias="readOnly")

    def patch(self, schema: "V1HostPathConnection"):
        self.host_path = schema.host_path or self.host_path
        self.mount_path = schema.mount_path or self.mount_path
        self.read_only = schema.read_only or self.read_only


class V1HostConnection(BaseSchemaModel):
    _IDENTIFIER = "host"

    url: StrictStr
    insecure: Optional[bool]

    def patch(self, schema: "V1HostConnection"):
        self.url = schema.url or self.url
        self.insecure = schema.insecure or self.insecure


class V1GitConnection(BaseSchemaModel):
    _IDENTIFIER = "git"

    url: Optional[StrictStr]
    revision: Optional[StrictStr]
    flags: Optional[List[StrictStr]]

    def get_name(self):
        if self.url:
            return self.url.split("/")[-1].split(".")[0]
        return None

    def patch(self, schema: "GitConnectionSchema"):
        self.url = schema.url or self.url
        self.revision = schema.revision or self.revision
        self.flags = schema.flags or self.flags


def patch_git(schema: Dict, gitSchema: V1GitConnection):
    if gitSchema.url:
        setattr(schema, "url", gitSchema.url)
    if gitSchema.revision:
        setattr(schema, "revision", gitSchema.revision)
    if gitSchema.flags:
        setattr(schema, "flags", gitSchema.flags)


class V1CustomConnection(BaseSchemaModel):
    _IDENTIFIER = "custom"

    @classmethod
    def from_dict(cls, value, partial: bool = False):
        return super().from_dict(value=value, partial=partial)

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1CustomConnection):
            return False

        return self.to_dict() == other.to_dict()

    def patch_git(self, schema: "GitConnectionSchema"):
        if schema.url:
            if "url" not in self._schema_keys:
                self._schema_keys.add("url")
            setattr(self, "url", schema.url)
        if schema.revision:
            if "revision" not in self._schema_keys:
                self._schema_keys.add("revision")
            setattr(self, "revision", schema.revision)

        if schema.flags:
            if "flags" not in self._schema_keys:
                self._schema_keys.add("flags")
            setattr(self, "flags", schema.flags)


def validate_connection(kind, definition):
    if kind not in V1ConnectionKind:
        raise ValueError("Connection with kind {} is not supported.".format(kind))

    if kind in V1ConnectionKind.blob_values():
        V1BucketConnection.from_dict(definition)

    if kind == V1ConnectionKind.VOLUME_CLAIM:
        V1ClaimConnection.from_dict(definition)

    if kind == V1ConnectionKind.HOST_PATH:
        V1HostPathConnection.from_dict(definition)

    if kind == V1ConnectionKind.REGISTRY:
        V1HostConnection.from_dict(definition)

    if kind == V1ConnectionKind.GIT:
        V1GitConnection.from_dict(definition)


V1Connection = Union[
    V1BucketConnection,
    V1ClaimConnection,
    V1HostPathConnection,
    V1HostConnection,
    V1GitConnection,
    Dict,
    RefField,
]
