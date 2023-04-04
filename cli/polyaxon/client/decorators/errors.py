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

from polyaxon.exceptions import handle_api_error
from polyaxon.logger import logger


def handle_client_error(
    e,
    message: Optional[str] = None,
    http_messages_mapping: Optional[Dict] = None,
    sys_exit: bool = False,
):
    handle_api_error(
        e=e,
        logger=logger,
        message=message,
        http_messages_mapping=http_messages_mapping,
        sys_exit=sys_exit,
    )
