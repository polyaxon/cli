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

import pytest

from mock import patch

from polyaxon.cli.version import upgrade, version
from polyaxon.schemas.api.compatibility import V1Compatibility
from polyaxon.schemas.api.installation import V1Installation
from polyaxon.schemas.api.version import V1Version
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliVersion(BaseCommandTestCase):
    @patch("polyaxon.cli.version.pip_upgrade")
    @patch("polyaxon.cli.version.sys")
    def test_upgrade(self, mock_sys, pip_upgrade):
        mock_sys.version = (
            "2.7.13 (default, Jan 19 2017, 14:48:08) \n[GCC 6.3.0 20170118]"
        )
        self.runner.invoke(upgrade)
        pip_upgrade.assert_called_once()

    @patch("polyaxon.sdk.api.VersionsV1Api.get_installation")
    @patch("polyaxon.sdk.api.VersionsV1Api.get_compatibility")
    @patch("polyaxon.cli.version.dict_tabulate")
    @patch("polyaxon.managers.cli.CliConfigManager.reset")
    def test_versions(
        self, config_rest, dict_tabulate, get_compatibility, get_installation
    ):
        get_compatibility.return_value = V1Compatibility(
            cli=V1Version(min="1.10.0", latest="20.0.0")
        )
        get_installation.return_value = V1Installation(version="1.12.2")
        self.runner.invoke(version, ["--check"])
        get_installation.assert_called_once()
        get_compatibility.assert_called_once()
        assert config_rest.call_count == 2
        assert dict_tabulate.call_count == 2
