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

from typing import List, Optional

from clipped.utils.lists import to_list

from polyaxon.auxiliaries import V1PolyaxonSidecarContainer
from polyaxon.connections import V1Connection
from polyaxon.containers.names import SIDECAR_CONTAINER
from polyaxon.env_vars.keys import EV_KEYS_ARTIFACTS_STORE_NAME, EV_KEYS_CONTAINER_ID
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.containers import patch_container
from polyaxon.polyflow import V1Plugins
from polyaxon.runner.converter import BaseConverter as _BaseConverter


class SidecarConverter(_BaseConverter):
    @classmethod
    def _get_sidecar_env_vars(
        cls,
        env_vars: List[k8s_schemas.V1EnvVar],
        container_id: str,
        artifacts_store_name: str,
    ) -> List[k8s_schemas.V1EnvVar]:
        env_vars = to_list(env_vars, check_none=True)[:]
        env_vars.append(cls._get_env_var(name=EV_KEYS_CONTAINER_ID, value=container_id))
        env_vars.append(
            cls._get_env_var(
                name=EV_KEYS_ARTIFACTS_STORE_NAME, value=artifacts_store_name
            )
        )
        return env_vars

    @staticmethod
    def _get_sidecar_args(
        container_id: str, sleep_interval: int, sync_interval: int, monitor_logs: bool
    ) -> List[str]:
        args = [
            "--container-id={}".format(container_id),
            "--sleep-interval={}".format(sleep_interval),
            "--sync-interval={}".format(sync_interval),
        ]
        if monitor_logs:
            args.append("--monitor-logs")
        return args

    @classmethod
    def _get_sidecar_container(
        cls,
        container_id: str,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        env: List[k8s_schemas.V1EnvVar],
        artifacts_store: V1Connection,
        plugins: V1Plugins,
        run_path: Optional[str],
    ) -> Optional[k8s_schemas.V1Container]:
        if artifacts_store and not plugins:
            raise PolyaxonConverterError(
                "Logs/artifacts store was passed and contexts was not passed."
            )

        has_artifacts = artifacts_store and plugins.collect_artifacts
        has_logs = artifacts_store and plugins.collect_logs

        if not has_logs and not has_artifacts:
            # No sidecar
            return None

        if (has_artifacts or has_logs) and not run_path:
            raise PolyaxonConverterError(
                "Logs store/outputs store must have a run_path."
            )

        env = cls._get_sidecar_env_vars(
            env_vars=env,
            container_id=container_id,
            artifacts_store_name=artifacts_store.name,
        )

        volume_mounts = cls._get_mounts(
            use_auth_context=plugins.auth,
            use_artifacts_context=has_artifacts,
            use_docker_context=False,
            use_shm_context=False,
        )

        sleep_interval = polyaxon_sidecar.sleep_interval
        sync_interval = polyaxon_sidecar.sync_interval
        monitor_logs = polyaxon_sidecar.monitor_logs
        if plugins and plugins.sidecar:
            if plugins.sidecar.sleep_interval:
                sleep_interval = plugins.sidecar.sleep_interval
            if plugins.sidecar.sync_interval:
                sync_interval = plugins.sidecar.sync_interval
            if plugins.sidecar.monitor_logs:
                monitor_logs = plugins.sidecar.monitor_logs
        sidecar_args = cls._get_sidecar_args(
            container_id=container_id,
            sleep_interval=sleep_interval,
            sync_interval=sync_interval,
            monitor_logs=monitor_logs,
        )

        env_from = []

        if artifacts_store.is_bucket:
            secret = artifacts_store.secret
            volume_mounts += to_list(
                cls._get_mount_from_resource(resource=secret), check_none=True
            )
            env += to_list(cls._get_items_from_secret(secret=secret), check_none=True)
            env_from += to_list(
                cls._get_env_from_secret(secret=secret), check_none=True
            )

            config_map = artifacts_store.config_map
            volume_mounts += to_list(
                cls._get_mount_from_resource(resource=config_map), check_none=True
            )
            env += to_list(
                cls._get_items_from_config_map(config_map=config_map), check_none=True
            )
            env_from += to_list(
                cls._get_env_from_config_map(config_map=config_map), check_none=True
            )
        else:
            volume_mounts += to_list(
                cls._get_mount_from_store(store=artifacts_store), check_none=True
            )
        # Add connections catalog env vars information
        env += to_list(
            cls._get_connections_catalog_env_var(connections=[artifacts_store]),
            check_none=True,
        )
        env += to_list(
            cls._get_connection_env_var(connection=artifacts_store),
            check_none=True,
        )

        container = k8s_schemas.V1Container(
            name=SIDECAR_CONTAINER,
            image=polyaxon_sidecar.get_image(),
            image_pull_policy=polyaxon_sidecar.image_pull_policy,
            command=["polyaxon", "sidecar"],
            args=sidecar_args,
            env=env,
            env_from=env_from,
            resources=polyaxon_sidecar.get_resources(),
            volume_mounts=volume_mounts,
        )

        return patch_container(container)
