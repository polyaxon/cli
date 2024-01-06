from typing import Optional

from polyaxon import settings
from polyaxon._connections import CONNECTION_CONFIG, V1Connection, V1ConnectionKind
from polyaxon._env_vars.getters import get_artifacts_store_name


def get_artifacts_connection() -> Optional[V1Connection]:
    store_name = get_artifacts_store_name(default=None)
    if store_name:
        return CONNECTION_CONFIG.get_connection_for(store_name)
    if settings.AGENT_CONFIG:
        return settings.AGENT_CONFIG.artifacts_store
    return None


def _get_fs_from_connection(
    connection: Optional[V1Connection],
    asynchronous: bool = False,
    use_listings_cache: bool = False,
    **kwargs
):
    # We assume that `None` refers to local store as well
    if not connection or connection.kind in {
        V1ConnectionKind.VOLUME_CLAIM,
        V1ConnectionKind.HOST_PATH,
    }:
        from fsspec.implementations.local import LocalFileSystem

        return LocalFileSystem(
            auto_mkdir=kwargs.get("auto_mkdir", True),
            use_listings_cache=use_listings_cache,
        )
    if connection.kind == V1ConnectionKind.WASB:
        from vents.providers.azure.blob_storage import BlobStorageService

        service = BlobStorageService.load_from_connection(connection)
        return service.get_fs(
            asynchronous=asynchronous, use_listings_cache=use_listings_cache, **kwargs
        )
    if connection.kind == V1ConnectionKind.S3:
        from vents.providers.aws.s3 import S3Service

        service = S3Service.load_from_connection(connection)
        return service.get_fs(
            asynchronous=asynchronous, use_listings_cache=use_listings_cache, **kwargs
        )
    if connection.kind == V1ConnectionKind.GCS:
        from vents.providers.gcp.gcs import GCSService

        service = GCSService.load_from_connection(connection)
        return service.get_fs(
            asynchronous=asynchronous, use_listings_cache=use_listings_cache, **kwargs
        )


async def get_async_fs_from_connection(connection: Optional[V1Connection], **kwargs):
    fs = _get_fs_from_connection(connection=connection, asynchronous=True, **kwargs)
    if fs.async_impl and hasattr(fs, "set_session"):
        await fs.set_session()
    return fs


def get_sync_fs_from_connection(connection: Optional[V1Connection], **kwargs):
    return _get_fs_from_connection(connection=connection, **kwargs)


def get_fs_from_name(connection_name: str, asynchronous: bool = False, **kwargs):
    connection = CONNECTION_CONFIG.get_connection_for(connection_name)
    return _get_fs_from_connection(
        connection=connection, asynchronous=asynchronous, **kwargs
    )


def get_sync_default_fs(**kwargs):
    connection = get_artifacts_connection()
    return get_sync_fs_from_connection(connection=connection, **kwargs)


async def get_default_fs(**kwargs):
    connection = get_artifacts_connection()
    return await get_async_fs_from_connection(connection=connection, **kwargs)


async def close_fs(fs):
    if hasattr(fs, "session") and hasattr(fs.session, "close"):
        try:
            await fs.session.close()
        except:  # noqa
            pass
    if hasattr(fs, "close_session"):
        try:
            fs.close_session(fs.loop, fs.session)
        except:  # noqa
            pass
    if hasattr(fs, "close"):
        try:
            await fs.close()
        except:  # noqa
            pass
