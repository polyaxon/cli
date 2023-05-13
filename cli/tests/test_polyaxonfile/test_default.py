import pytest
import tempfile

from polyaxon.polyaxonfile import (
    DEFAULT_POLYAXON_FILE_EXTENSION,
    DEFAULT_POLYAXON_FILE_NAME,
    check_default_path,
)
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.polyaxonfile_mark
class TestDefaultFile(BaseTestCase):
    def test_default_not_found(self):
        path = tempfile.mkdtemp()
        assert check_default_path(path=path) is None

    def test_polyaxon_found(self):
        def create_file(path, filename, ext):
            fpath = "{}/{}.{}".format(path, filename, ext)
            open(fpath, "w")

        for filename in DEFAULT_POLYAXON_FILE_NAME:
            for ext in DEFAULT_POLYAXON_FILE_EXTENSION:
                path = tempfile.mkdtemp()
                create_file(path, filename, ext)
                assert check_default_path(path=path)
