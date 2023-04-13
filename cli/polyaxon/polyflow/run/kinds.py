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
from clipped.utils.enums import PEnum


class V1RunKind(str, PEnum):
    JOB = "job"
    SERVICE = "service"
    DAG = "dag"
    SPARK = "spark"
    DASK = "dask"
    FLINK = "flink"
    RAY = "ray"
    MPIJOB = "mpijob"
    TFJOB = "tfjob"
    PYTORCHJOB = "pytorchjob"
    PADDLEJOB = "paddlejob"
    MXJOB = "mxjob"
    XGBJOB = "xgbjob"
    MATRIX = "matrix"
    SCHEDULE = "schedule"
    TUNER = "tuner"
    WATCHDOG = "watchdog"
    NOTIFIER = "notifier"
    CLEANER = "cleaner"
    BUILDER = "builder"

    @classmethod
    def eager_values(cls):
        return {
            cls.MATRIX,
        }

    @classmethod
    def default_runtime_values(cls):
        return {
            cls.JOB,
            cls.SERVICE,
            cls.MPIJOB,
            cls.TFJOB,
            cls.PYTORCHJOB,
            cls.MXJOB,
            cls.PADDLEJOB,
            cls.XGBJOB,
            cls.NOTIFIER,
            cls.WATCHDOG,
            cls.TUNER,
            cls.CLEANER,
            cls.BUILDER,
        }


class V1CloningKind(str, PEnum):
    COPY = "copy"
    RESTART = "restart"
    CACHE = "cache"


class V1PipelineKind(str, PEnum):
    DAG = "dag"
    MATRIX = "matrix"


class V1RunEdgeKind(str, PEnum):
    ACTION = "action"
    EVENT = "event"
    HOOK = "hook"
    DAG = "dag"
    JOIN = "join"
    RUN = "run"
    TB = "tb"
    BUILD = "build"
