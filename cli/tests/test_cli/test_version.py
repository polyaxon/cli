import pytest

from mock import patch

from polyaxon._cli.version import upgrade, version
from polyaxon._schemas.compatibility import V1Compatibility
from polyaxon._schemas.installation import V1Installation
from polyaxon._schemas.version import V1Version
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliVersion(BaseCommandTestCase):
    @patch("polyaxon._cli.version.pip_upgrade")
    @patch("polyaxon._cli.version.sys")
    def test_upgrade(self, mock_sys, pip_upgrade):
        mock_sys.version = (
            "2.7.13 (default, Jan 19 2017, 14:48:08) \n[GCC 6.3.0 20170118]"
        )
        self.runner.invoke(upgrade)
        pip_upgrade.assert_called_once()

    @patch("polyaxon._sdk.api.VersionsV1Api.get_installation")
    @patch("polyaxon._sdk.api.VersionsV1Api.get_compatibility")
    @patch("polyaxon._cli.version.Printer.dict_tabulate")
    @patch("polyaxon._managers.cli.CliConfigManager.reset")
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
