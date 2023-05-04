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

from polyaxon.converter.converters.base import BaseConverter, ConverterAbstract
from polyaxon.converter.converters.helpers import (
    CleanerConverter,
    NotifierConverter,
    TunerConverter,
)
from polyaxon.converter.converters.job import JobConverter
from polyaxon.converter.converters.kubeflow import (
    MPIJobConverter,
    MXJobConverter,
    PaddleJobConverter,
    PytorchJobConverter,
    TfJobConverter,
    XGBoostJobConverter,
)
from polyaxon.converter.converters.service import ServiceConverter
from polyaxon.polyflow import V1RunKind

CONVERTERS = {
    V1RunKind.CLEANER: CleanerConverter,
    V1RunKind.NOTIFIER: NotifierConverter,
    V1RunKind.TUNER: TunerConverter,
    V1RunKind.JOB: JobConverter,
    V1RunKind.SERVICE: ServiceConverter,
    V1RunKind.MPIJOB: MPIJobConverter,
    V1RunKind.TFJOB: TfJobConverter,
    V1RunKind.PADDLEJOB: PaddleJobConverter,
    V1RunKind.PYTORCHJOB: PytorchJobConverter,
    V1RunKind.MXJOB: MXJobConverter,
    V1RunKind.XGBJOB: XGBoostJobConverter,
}
