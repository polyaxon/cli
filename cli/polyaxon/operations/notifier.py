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
from typing import Dict, Union

from polyaxon.auxiliaries import get_default_notification_container
from polyaxon.polyflow import (
    V1IO,
    V1Component,
    V1NotifierJob,
    V1Operation,
    V1Param,
    V1Plugins,
    V1Termination,
)


def get_notifier_operation(
    connection: str,
    backend: str,
    owner: str,
    project: str,
    run_uuid: str,
    run_name: str,
    condition: Union[str, Dict],
) -> V1Operation:
    return V1Operation(
        params={
            "backend": V1Param.construct(value=backend),
            "owner": V1Param.construct(value=owner),
            "project": V1Param.construct(value=project),
            "uuid": V1Param.construct(value=run_uuid),
            "name": V1Param.construct(value=run_name),
            "condition": V1Param.construct(value=condition),
        },
        termination=V1Termination.construct(max_retries=3),
        component=V1Component.construct(
            name="notifier",
            plugins=V1Plugins.construct(
                auth=False,
                collect_logs=False,
                collect_artifacts=False,
                collect_resources=False,
                auto_resume=False,
                sync_statuses=False,
                external_host=True,
            ),
            inputs=[
                V1IO.construct(name="backend", type="str", is_optional=False),
                V1IO.construct(name="owner", type="str", is_optional=False),
                V1IO.construct(name="project", type="str", is_optional=False),
                V1IO.construct(name="uuid", type="str", is_optional=False),
                V1IO.construct(name="name", type="str", is_optional=True),
                V1IO.construct(name="condition", type="dict", is_optional=True),
                V1IO.construct(name="connection", type="str", is_optional=True),
            ],
            run=V1NotifierJob.construct(
                connections=[connection],
                container=get_default_notification_container(),
            ),
        ),
    )
