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
from typing import Dict, Optional

from polyaxon.compiler.resolver import AgentResolver
from polyaxon.k8s import converter
from polyaxon.polyaxonfile import CompiledOperationSpecification, OperationSpecification
from polyaxon.schemas.cli.agent_config import AgentConfig


def convert(
    owner_name: str,
    project_name: str,
    run_name: str,
    run_uuid: str,
    content: str,
    default_auth: bool,
    agent_content: Optional[str] = None,
) -> Dict:
    agent_env = AgentResolver.construct()
    compiled_operation = CompiledOperationSpecification.read(content)

    agent_env.resolve(
        compiled_operation=compiled_operation,
        agent_config=AgentConfig.read(agent_content) if agent_content else None,
    )
    return converter.convert(
        compiled_operation=compiled_operation,
        owner_name=owner_name,
        project_name=project_name,
        run_name=run_name,
        run_uuid=run_uuid,
        namespace=agent_env.namespace,
        polyaxon_init=agent_env.polyaxon_init,
        polyaxon_sidecar=agent_env.polyaxon_sidecar,
        run_path=run_uuid,
        artifacts_store=agent_env.artifacts_store,
        connection_by_names=agent_env.connection_by_names,
        secrets=agent_env.secrets,
        config_maps=agent_env.config_maps,
        default_sa=agent_env.default_sa,
        default_auth=default_auth,
    )


def make_and_convert(
    owner_name: str,
    project_name: str,
    run_uuid: str,
    run_name: str,
    content: str,
    default_auth: bool = False,
):
    operation = OperationSpecification.read(content)
    compiled_operation = OperationSpecification.compile_operation(operation)
    return converter.make(
        owner_name=owner_name,
        project_name=project_name,
        project_uuid=project_name,
        run_uuid=run_uuid,
        run_name=run_name,
        run_path=run_uuid,
        compiled_operation=compiled_operation,
        params=operation.params,
        default_auth=default_auth,
    )
