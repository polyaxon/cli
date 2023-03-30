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

from polyaxon.sdk.async_client.api_client import AsyncApiClient
from polyaxon.sdk.sync_client.api_client import ApiClient


class BaseApi:
    def __init__(self, api_client=None, is_async=False):
        if api_client is None:
            api_client = (
                AsyncApiClient.get_default() if is_async else ApiClient.get_default()
            )
        self.api_client = api_client
