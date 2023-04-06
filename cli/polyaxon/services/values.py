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
import os

from typing import Optional

from clipped.enums_utils import PEnum

from polyaxon.env_vars.keys import EV_KEYS_SERVICE

SERVICE = None


class PolyaxonServices(str, PEnum):
    PLATFORM = "platform"
    AUTH = "auth"
    UI = "ui"
    API = "api"
    GATEWAY = "gateway"
    STREAMS = "streams"
    SANDBOX = "sandbox"
    CLI = "cli"
    INITIALIZER = "initializer"
    INIT = "init"
    SIDECAR = "sidecar"
    RUNNER = "runner"
    AGENT = "agent"
    OPERATOR = "operator"
    BILLING = "billing"
    HP_SEARCH = "hp_search"
    EVENTS_HANDLER = "events-handlers"

    @classmethod
    def agent_values(cls):
        return [
            cls.PLATFORM,
            cls.CLI,
            cls.UI,
            cls.OPERATOR,
            cls.AGENT,
            cls.INITIALIZER,
            cls.SIDECAR,
        ]

    @classmethod
    def get_service_name(cls):
        global SERVICE

        return SERVICE

    @classmethod
    def set_service_name(cls, value: Optional[str] = None):
        global SERVICE

        SERVICE = value or os.environ.get(EV_KEYS_SERVICE)

    @classmethod
    def is_agent(cls, value: Optional[str] = None):
        return cls.AGENT == (value or cls.get_service_name())

    @classmethod
    def is_sandbox(cls, value: Optional[str] = None):
        return cls.SANDBOX == (value or cls.get_service_name())

    @classmethod
    def is_hp_search(cls, value: Optional[str] = None):
        return cls.HP_SEARCH == (value or cls.get_service_name())

    @classmethod
    def is_init(cls, value: Optional[str] = None):
        return (value or cls.get_service_name()) in {cls.INIT, cls.INITIALIZER}

    @classmethod
    def is_sidecar(cls, value: Optional[str] = None):
        return cls.SIDECAR == (value or cls.get_service_name())

    @classmethod
    def is_streams(cls, value: Optional[str] = None):
        return cls.STREAMS == (value or cls.get_service_name())

    @classmethod
    def is_api(cls, value: Optional[str] = None):
        return cls.API == (value or cls.get_service_name())

    @classmethod
    def is_gateway(cls, value: Optional[str] = None):
        return cls.GATEWAY == (value or cls.get_service_name())

    @classmethod
    def is_events_handlers(cls, value: Optional[str] = None):
        return cls.EVENTS_HANDLER == (value or cls.get_service_name())
