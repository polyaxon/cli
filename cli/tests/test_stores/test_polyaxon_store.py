from mock import mock, patch
import os
import pytest
import tarfile
import uuid

from clipped.utils.paths import check_or_create_path
from polyaxon import settings
from polyaxon._managers.ignore import IgnoreConfigManager
from polyaxon._utils.test_utils import AsyncMock, BaseTestCase, patch_settings
from polyaxon.client import AsyncPolyaxonStore, PolyaxonStore, RunClient
from polyaxon.exceptions import PolyaxonClientException


class StoreConfig:
    def get_full_headers(self, headers=None):
        return headers or {}


class StoreClient:
    def __init__(self, run_uuid):
        self.run_uuid = run_uuid
        self.client = mock.Mock(config=StoreConfig())


@pytest.mark.parametrize("mode", ["resolve-safe", "resolve-all", "skip"])
def test_upload_directory_symlink_archive_contents(tmp_path, monkeypatch, mode):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".polyaxonignore").write_text("*.skip\n")
    source = tmp_path / "source"
    source.mkdir()
    (source / "content.txt").write_text("content")
    (source / "ignored.skip").write_text("excluded")
    (tmp_path / "file-link").symlink_to("source/content.txt")
    (tmp_path / "directory-link").symlink_to("source", target_is_directory=True)
    store = PolyaxonStore(StoreClient(uuid.uuid4().hex))
    captured = {}

    def capture_upload(url, files, files_size, json_data):
        stream = files[0][1][1]
        captured["path"] = stream.name
        with tarfile.open(fileobj=stream, mode="r:gz") as archive:
            captured["members"] = {
                member.name: member for member in archive.getmembers()
            }
            captured["contents"] = {
                member.name: archive.extractfile(member).read()
                for member in archive.getmembers()
                if member.isfile()
            }
        return "uploaded"

    store.upload = mock.Mock(side_effect=capture_upload)
    files = IgnoreConfigManager.get_unignored_filepaths(
        str(tmp_path), symlink_mode=mode
    )
    result = store.upload_dir(
        url="url",
        files=files,
        relative_to=str(tmp_path),
        dereference=mode in ("resolve-safe", "resolve-all"),
        recursive=False,
    )

    assert result == "uploaded"
    assert not os.path.exists(captured["path"])
    members = captured["members"]
    assert captured["contents"]["source/content.txt"] == b"content"
    assert not any(name.endswith(".skip") for name in members)
    if mode in ("resolve-safe", "resolve-all"):
        assert members["directory-link"].isdir()
        assert captured["contents"]["directory-link/content.txt"] == b"content"
        assert captured["contents"]["file-link"] == b"content"
        assert all(member.isfile() or member.isdir() for member in members.values())
    else:
        assert "file-link" not in members
        assert "directory-link" not in members


def test_upload_file_list_retains_archive_defaults(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "content.txt").write_text("content")
    link = tmp_path / "link"
    link.symlink_to("source", target_is_directory=True)
    store = PolyaxonStore(StoreClient(uuid.uuid4().hex))

    def capture_upload(url, files, files_size, json_data):
        with tarfile.open(fileobj=files[0][1][1], mode="r:gz") as archive:
            assert set(archive.getnames()) == {"source", "source/content.txt", "link"}
            assert archive.getmember("link").issym()

    store.upload = mock.Mock(side_effect=capture_upload)
    store.upload_dir(
        url="url", files=[str(source), str(link)], relative_to=str(tmp_path)
    )
    store.upload.assert_called_once()


class FakeContent:
    def __init__(self, chunks):
        self.chunks = chunks

    async def iter_chunked(self, chunk_size):
        for chunk in self.chunks:
            yield chunk


class FakeResponse:
    status = 200

    def __init__(self, chunks, headers=None):
        self.headers = headers or {}
        self.content = FakeContent(chunks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def text(self):
        return ""


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class TestPolyaxonStore(BaseTestCase):
    def test_download_file(self):
        run_uuid = uuid.uuid4().hex
        store = PolyaxonStore(
            client=RunClient(owner="test", project="test", run_uuid=run_uuid)
        )
        with patch("polyaxon._client.store.PolyaxonStore.download") as mock_call:
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

        with patch("polyaxon._client.store.PolyaxonStore.download") as mock_call:
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

        with patch("polyaxon._client.store.PolyaxonStore.download") as mock_call:
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


@pytest.mark.asyncio
async def test_async_download_file():
    patch_settings()
    run_uuid = uuid.uuid4().hex
    store = AsyncPolyaxonStore(client=StoreClient(run_uuid))
    store.download = AsyncMock()

    result = await store.download_file(url="url", path="test/path")

    assert result == "{}/{}/test/path".format(
        settings.CLIENT_CONFIG.archives_root, run_uuid
    )
    assert store.download.call_count == 1
    assert store.download.call_args_list[0][1] == {
        "filename": result,
        "params": {"path": "test/path"},
        "url": "url",
    }


@pytest.mark.asyncio
async def test_async_download_file_skips_existing_local_path():
    patch_settings()
    run_uuid = uuid.uuid4().hex
    local_path = os.path.join(
        settings.CLIENT_CONFIG.archives_root,
        run_uuid,
        "test/path",
    )
    check_or_create_path(local_path, is_dir=False)
    with open(local_path, "wb") as f:
        f.write(b"cached")
    store = AsyncPolyaxonStore(client=StoreClient(run_uuid))
    store.download = AsyncMock()

    result = await store.download_file(url="url", path="test/path")

    assert result == local_path
    assert store.download.call_count == 0


@pytest.mark.asyncio
async def test_async_download_streams_response_to_file(tmp_path):
    patch_settings()
    filename = str(tmp_path / "artifact.txt")
    response = FakeResponse(
        chunks=[b"abc", b"def"],
        headers={"content-length": "6"},
    )
    session = FakeSession(response=response)
    store = AsyncPolyaxonStore(client=StoreClient(uuid.uuid4().hex))

    result = await store.download(
        url="url",
        filename=filename,
        params={"path": "artifact.txt"},
        headers={"x-test": "1"},
        session=session,
        show_progress=False,
    )

    assert result == filename
    assert (tmp_path / "artifact.txt").read_bytes() == b"abcdef"
    assert session.calls[0]["url"] == "url"
    assert session.calls[0]["params"] == {"path": "artifact.txt"}
    assert session.calls[0]["headers"] == {"x-test": "1"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,args",
    [
        ("upload", ()),
        ("upload_file", ()),
        ("upload_dir", ()),
    ],
)
async def test_async_upload_methods_raise(method, args):
    patch_settings()
    store = AsyncPolyaxonStore(client=StoreClient(uuid.uuid4().hex))

    with pytest.raises(PolyaxonClientException):
        await getattr(store, method)(*args)
