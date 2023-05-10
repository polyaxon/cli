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

from clipped.utils.validation import validate_tags

from polyaxon.schemas.types import V1TensorboardType

TENSORBOARD_INIT_COMMAND = ["polyaxon", "initializer", "tensorboard"]


def get_tensorboard_args(
    tb_args: V1TensorboardType, context_from: str, context_to: str, connection_kind: str
):
    args = [
        "--context-from={}".format(context_from),
        "--context-to={}".format(context_to),
        "--connection-kind={}".format(connection_kind),
    ]
    if tb_args.port:
        args.append("--port={}".format(tb_args.port))
    if tb_args.uuids:
        uuids = validate_tags(tb_args.uuids, validate_yaml=True)
        args.append("--uuids={}".format(",".join(uuids)))
    if tb_args.use_names:
        args.append("--use-names")
    if tb_args.path_prefix:
        args.append("--path-prefix={}".format(tb_args.path_prefix)),
    if tb_args.plugins:
        plugins = validate_tags(tb_args.plugins, validate_yaml=True)
        args.append("--plugins={}".format(",".join(plugins)))

    return args
