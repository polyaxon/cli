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
import copy

from typing import Dict, Optional

from polyaxon.compiler.contexts.base import BaseContextsManager
from polyaxon.connections import V1Connection
from polyaxon.polyflow import V1CompiledOperation, V1KFReplica, V1MXJob


class MXJobContextsManager(BaseContextsManager):
    @classmethod
    def resolve(
        cls,
        namespace: str,
        owner_name: str,
        project_name: str,
        run_uuid: str,
        contexts: Dict,
        compiled_operation: V1CompiledOperation,
        connection_by_names: Dict[str, V1Connection],
    ) -> Dict:
        contexts["init"] = {}
        contexts["connections"] = {}
        job = compiled_operation.run  # type: V1MXJob

        def _get_replica(replica: Optional[V1KFReplica]) -> Dict:
            if not replica:
                return contexts
            return cls._resolver_replica(
                contexts={"globals": copy.copy(contexts["globals"])},
                init=replica.init,
                connections=replica.connections,
                connection_by_names=connection_by_names,
            )

        return {
            "scheduler": _get_replica(job.scheduler),
            "server": _get_replica(job.server),
            "worker": _get_replica(job.worker),
            "tuner": _get_replica(job.tuner),
            "tuner_server": _get_replica(job.tuner_server),
            "tuner_tracker": _get_replica(job.tuner_tracker),
        }
