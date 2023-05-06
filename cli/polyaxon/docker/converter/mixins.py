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
from typing import Dict

from polyaxon.containers.names import MAIN_JOB_CONTAINER
from polyaxon.polyflow import V1RunKind


class JobMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.JOB
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class NotifierMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.NOTIFIER
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class CleanerMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.CLEANER
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class TunerMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.TUNER
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class ServiceMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.SERVICE
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


MIXIN_MAPPING: Dict = {
    V1RunKind.JOB: JobMixin,
    V1RunKind.NOTIFIER: NotifierMixin,
    V1RunKind.CLEANER: CleanerMixin,
    V1RunKind.TUNER: TunerMixin,
    V1RunKind.SERVICE: ServiceMixin,
}
