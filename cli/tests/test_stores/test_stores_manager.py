import os
import pytest

from clipped.utils.paths import check_or_create_path

from polyaxon import settings
from polyaxon.fs.async_manager import delete_file_or_dir, download_dir, download_file
from polyaxon.fs.fs import get_default_fs
from polyaxon.utils.test_utils import create_tmp_files, set_store


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_download_dir_archive():
    store_root = set_store()
    path = os.path.join(store_root, "foo")
    check_or_create_path(path, is_dir=True)
    create_tmp_files(path)
    fs = await get_default_fs()
    await download_dir(
        fs=fs, store_path=settings.AGENT_CONFIG.store_root, subpath="foo", to_tar=True
    )

    path_to = os.path.join(settings.AGENT_CONFIG.local_root, "foo")
    assert os.path.exists(path_to)
    assert os.path.exists(path_to + "/file0.txt")
    assert os.path.exists(path_to + "/file1.txt")
    tar_path = os.path.join(settings.CLIENT_CONFIG.archives_root, "foo.tar.gz")
    assert os.path.exists(tar_path)


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_download_file():
    store_root = set_store()
    path = os.path.join(store_root, "foo")
    check_or_create_path(path, is_dir=True)
    create_tmp_files(path)
    fs = await get_default_fs()
    await download_file(
        fs=fs,
        store_path=settings.AGENT_CONFIG.store_root,
        subpath="foo/file0.txt",
        check_cache=False,
    )

    path_to = os.path.join(settings.AGENT_CONFIG.local_root, "foo/file0.txt")
    assert os.path.exists(path_to)


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_delete_file():
    store_root = set_store()
    path = os.path.join(store_root, "foo")
    check_or_create_path(path, is_dir=True)
    create_tmp_files(path)
    filepath = "{}/file0.txt".format(path)
    assert os.path.exists(path) is True
    assert os.path.exists(filepath) is True
    fs = await get_default_fs()
    await delete_file_or_dir(
        fs=fs,
        store_path=settings.AGENT_CONFIG.store_root,
        subpath="foo/file0.txt",
        is_file=True,
    )
    assert os.path.exists(path) is True
    assert os.path.exists(filepath) is False


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_delete_dir():
    store_root = set_store()
    path = os.path.join(store_root, "foo")
    check_or_create_path(path, is_dir=True)
    create_tmp_files(path)
    filepath = "{}/file0.txt".format(path)
    assert os.path.exists(path) is True
    assert os.path.exists(filepath) is True
    assert os.path.exists(filepath) is True
    fs = await get_default_fs()
    await delete_file_or_dir(
        fs=fs, store_path=settings.AGENT_CONFIG.store_root, subpath="foo", is_file=False
    )
    assert os.path.exists(path) is False
    assert os.path.exists(filepath) is False
