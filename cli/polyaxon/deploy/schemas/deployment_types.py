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

from polyaxon.utils.enums_utils import PEnum


class DeploymentTypes(str, PEnum):
    KUBERNETES = "kubernetes"
    MINIKUBE = "minikube"
    MICRO_K8S = "microk8s"
    DOCKER_COMPOSE = "docker-compose"
    DOCKER = "docker"
    HEROKU = "heroku"


class DeploymentCharts(str, PEnum):
    PLATFORM = "platform"
    AGENT = "agent"
    GATEWAY = "gateway"
