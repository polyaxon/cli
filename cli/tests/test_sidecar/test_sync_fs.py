import pytest

from fsspec.implementations.local import LocalFileSystem

from polyaxon._fs.watcher import FSWatcher
from polyaxon._sidecar.container.monitors.artifacts import sync_fs


@pytest.mark.asyncio
async def test_deleted_files_are_removed_from_local_stores(tmp_path):
    run_path = tmp_path / "context" / "uuid"
    run_path.mkdir(parents=True)
    store_path = tmp_path / "store"
    store_path.mkdir()
    fs = LocalFileSystem(auto_mkdir=True)
    fw = FSWatcher()

    async def sync():
        fw.init()
        fw.sync(str(run_path))
        await sync_fs(fs=fs, fw=fw, store_base_path=str(store_path))

    (run_path / "keep.txt").write_text("keep")
    (run_path / "drop.txt").write_text("drop")
    await sync()
    assert (store_path / "uuid" / "drop.txt").exists()

    (run_path / "drop.txt").unlink()
    await sync()

    assert (store_path / "uuid" / "keep.txt").exists()
    assert not (store_path / "uuid" / "drop.txt").exists()
