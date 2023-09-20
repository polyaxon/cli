import pytest

from polyaxon._schemas.types.file import V1FileType
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.init_mark
class TestFileInitConfigs(BaseTestCase):
    def test_file_type(self):
        config_dict = {
            "filename": "script.py",
            "kind": "file",
            "chmod": "+x",
            "content": "test",
        }
        config = V1FileType.from_dict(config_dict)
        assert config.to_dict() == config_dict
