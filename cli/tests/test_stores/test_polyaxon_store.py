import uuid

from mock import patch

from polyaxon import settings
from polyaxon.client import RunClient
from polyaxon.stores.polyaxon_store import PolyaxonStore
from polyaxon.utils.test_utils import BaseTestCase


class TestPolyaxonStore(BaseTestCase):
    def test_download_file(self):
        run_uuid = uuid.uuid4().hex
        store = PolyaxonStore(
            client=RunClient(owner="test", project="test", run_uuid=run_uuid)
        )
        with patch(
            "polyaxon.stores.polyaxon_store.PolyaxonStore.download"
        ) as mock_call:
            result = store.download_file(url="url", path="test/path")

        assert result == "{}/{}/test/path".format(
            settings.CLIENT_CONFIG.archives_root, run_uuid
        )
        assert mock_call.call_count == 1
        assert mock_call.call_args_list[0][1] == {
            "filename": result,
            "params": {"path": "test/path"},
            "url": "url",
        }

        with patch(
            "polyaxon.stores.polyaxon_store.PolyaxonStore.download"
        ) as mock_call:
            result = store.download_file(url="url", path="test/path", untar=False)

        assert result == "{}/{}/test/path".format(
            settings.CLIENT_CONFIG.archives_root, run_uuid
        )
        assert mock_call.call_count == 1
        assert mock_call.call_args_list[0][1] == {
            "filename": result,
            "untar": False,
            "params": {"path": "test/path"},
            "url": "url",
        }

        with patch(
            "polyaxon.stores.polyaxon_store.PolyaxonStore.download"
        ) as mock_call:
            result = store.download_file(url="url", path="test/path", untar=True)

        assert result == "{}/{}/test/path".format(
            settings.CLIENT_CONFIG.archives_root, run_uuid
        )
        assert mock_call.call_count == 1
        assert mock_call.call_args_list[0][1] == {
            "filename": result,
            "untar": True,
            "params": {"path": "test/path"},
            "url": "url",
        }
