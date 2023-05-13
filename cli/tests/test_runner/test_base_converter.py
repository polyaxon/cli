import os
import pytest

from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1HostPathConnection,
)
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.runner.converter.init.artifacts import get_artifacts_store_args
from polyaxon.runner.converter.init.git import get_repo_context_args
from polyaxon.runner.converter.init.store import (
    cp_mount_args,
    cp_store_args,
    get_or_create_args,
    get_volume_args,
)
from polyaxon.schemas.types import V1ArtifactsType
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.agent_mark
class TestBaseConverter(BaseTestCase):
    def test_get_or_create_args(self):
        assert (
            get_or_create_args(path="/foo")
            == 'if [ ! -d "/foo" ]; then mkdir -m 0777 -p /foo; fi;'
        )

    def test_cp_store_args(self):
        assert (
            cp_mount_args(
                path_from="/foo",
                path_to="/bar",
                is_file=True,
                sync_fw=False,
            )
            == "if [ -f /foo ]; then cp /foo /bar;  fi;"
        )
        assert (
            cp_mount_args(
                path_from="/foo",
                path_to="/bar",
                is_file=False,
                sync_fw=False,
            )
            == 'if [ -d /foo ] && [ "$(ls -A /foo)" ]; then cp -R /foo/* /bar;  fi;'
        )
        assert cp_store_args(
            backend="host_path",
            connection="conn",
            path_from="/foo",
            path_to="/bar",
            is_file=False,
            sync_fw=False,
            check_path=True,
        ) == (
            "polyaxon initializer path --connection-name=conn --connection-kind=host_path "
            "--path-from=/foo --path-to=/bar --check-path;"
        )

    def test_files_cp_gcs_args(self):
        assert cp_store_args(
            backend="gcs",
            connection="conn",
            path_from="gcs://foo",
            path_to="/local",
            is_file=True,
            sync_fw=False,
            check_path=False,
        ) == (
            "polyaxon initializer path --connection-name=conn --connection-kind=gcs "
            "--path-from=gcs://foo --path-to=/local --is-file;"
        )

    def test_dirs_cp_gcs_args(self):
        assert cp_store_args(
            backend="gcs",
            connection="conn",
            path_from="gcs://foo",
            path_to="/local",
            is_file=False,
            sync_fw=False,
            check_path=True,
        ) == (
            "polyaxon initializer path --connection-name=conn --connection-kind=gcs "
            "--path-from=gcs://foo --path-to=/local --check-path;"
        )

    def test_files_cp_wasb_args(self):
        assert cp_store_args(
            backend="wasb",
            connection="conn",
            path_from="wasb://foo",
            path_to="/local",
            is_file=True,
            sync_fw=False,
            check_path=False,
        ) == (
            "polyaxon initializer path --connection-name=conn --connection-kind=wasb "
            "--path-from=wasb://foo --path-to=/local --is-file;"
        )

    def test_cp_wasb_args(self):
        assert cp_store_args(
            backend="wasb",
            connection="conn",
            path_from="wasb://foo",
            path_to="/local",
            is_file=False,
            sync_fw=False,
            check_path=True,
        ) == (
            "polyaxon initializer path --connection-name=conn --connection-kind=wasb "
            "--path-from=wasb://foo --path-to=/local --check-path;"
        )

    def test_get_volume_args_s3(self):
        s3_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        path_to = "/path-to/"
        path_from = os.path.join(s3_store.store_path, "")
        assert get_volume_args(s3_store, path_to, None, None) == " ".join(
            [
                get_or_create_args(path=path_to),
                cp_store_args(
                    backend="s3",
                    connection=s3_store.name,
                    path_from=path_from,
                    path_to=path_to,
                    is_file=False,
                    sync_fw=False,
                    check_path=False,
                ),
            ]
        )

        s3_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        base_path = "/path/to/"
        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_from1 = os.path.join(s3_store.store_path, "path1")
        path_from2 = os.path.join(s3_store.store_path, "path2")
        assert get_volume_args(
            s3_store,
            "/path/to",
            artifacts=V1ArtifactsType(files=["path1", "path2"]),
            paths=None,
        ) == " ".join(
            [
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend="s3",
                    connection=s3_store.name,
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=True,
                    sync_fw=False,
                    check_path=False,
                ),
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend="s3",
                    connection=s3_store.name,
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=True,
                    sync_fw=False,
                    check_path=False,
                ),
            ]
        )

        base_path = "/path/to/"
        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_from1 = os.path.join(s3_store.store_path, "path1")
        path_from2 = os.path.join(s3_store.store_path, "path2")
        assert get_volume_args(
            s3_store,
            "/path/to",
            artifacts=None,
            paths=["path1", "path2"],
        ) == " ".join(
            [
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend="s3",
                    connection=s3_store.name,
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=False,
                    sync_fw=False,
                    check_path=True,
                ),
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend="s3",
                    connection=s3_store.name,
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=False,
                    sync_fw=False,
                    check_path=True,
                ),
            ]
        )

    def test_get_volume_args_gcs(self):
        gcs_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
        )
        path_to = "/path/to/"
        path_from = os.path.join(gcs_store.store_path, "")
        assert get_volume_args(gcs_store, path_to, None, None) == " ".join(
            [
                get_or_create_args(path=path_to),
                cp_store_args(
                    backend="gcs",
                    connection=gcs_store.name,
                    path_from=path_from,
                    path_to=path_to,
                    is_file=False,
                    sync_fw=False,
                    check_path=False,
                ),
            ]
        )

        gcs_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="Congs//:foo"),
        )

        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_from1 = os.path.join(gcs_store.store_path, "path1")
        path_from2 = os.path.join(gcs_store.store_path, "path2")
        assert get_volume_args(
            gcs_store,
            "/path/to",
            artifacts=V1ArtifactsType(dirs=["path1", "path2"]),
            paths=None,
        ) == " ".join(
            [
                get_or_create_args(path=path_to1),
                cp_store_args(
                    backend="gcs",
                    connection=gcs_store.name,
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=False,
                    sync_fw=False,
                    check_path=False,
                ),
                get_or_create_args(path=path_to2),
                cp_store_args(
                    backend="gcs",
                    connection=gcs_store.name,
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=False,
                    sync_fw=False,
                    check_path=False,
                ),
            ]
        )

    def test_get_volume_args_az(self):
        az_store = V1Connection(
            name="test_az",
            kind=V1ConnectionKind.WASB,
            schema_=V1BucketConnection(bucket="wasb://x@y.blob.core.windows.net"),
        )
        path_to = "/path/to/"
        path_from = os.path.join(az_store.store_path, "")
        assert get_volume_args(az_store, path_to, None, None) == " ".join(
            [
                get_or_create_args(path=path_to),
                cp_store_args(
                    backend="wasb",
                    connection=az_store.name,
                    path_from=path_from,
                    path_to=path_to,
                    is_file=False,
                    sync_fw=False,
                    check_path=False,
                ),
            ]
        )

        az_store = V1Connection(
            name="test_az",
            kind=V1ConnectionKind.WASB,
            schema_=V1BucketConnection(bucket="wasb://x@y.blob.core.windows.net"),
        )
        base_path = "/path/to/"
        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_from1 = os.path.join(az_store.store_path, "path1")
        path_from2 = os.path.join(az_store.store_path, "path2")
        assert get_volume_args(
            az_store,
            "/path/to",
            artifacts=V1ArtifactsType(files=["path1"], dirs=["path2"]),
            paths=None,
        ) == " ".join(
            [
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend="wasb",
                    connection=az_store.name,
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=True,
                    sync_fw=False,
                    check_path=False,
                ),
                get_or_create_args(path=path_to2),
                cp_store_args(
                    backend="wasb",
                    connection=az_store.name,
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=False,
                    sync_fw=False,
                    check_path=False,
                ),
            ]
        )

    def test_get_volume_args_claim(self):
        claim_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        path_to = "/path/to/"
        path_from = os.path.join(claim_store.store_path, "")
        assert get_volume_args(claim_store, path_to, None, None) == " ".join(
            [
                get_or_create_args(path=path_to),
                cp_mount_args(
                    path_from=path_from,
                    path_to=path_to,
                    is_file=False,
                    sync_fw=False,
                ),
            ]
        )

        claim_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        base_path = "/path/to/"
        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_from1 = os.path.join(claim_store.store_path, "path1")
        path_from2 = os.path.join(claim_store.store_path, "path2")
        assert get_volume_args(
            claim_store,
            "/path/to",
            artifacts=V1ArtifactsType(files=["path1", "path2"]),
            paths=None,
        ) == " ".join(
            [
                get_or_create_args(path=base_path),
                cp_mount_args(
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=True,
                    sync_fw=False,
                ),
                get_or_create_args(path=base_path),
                cp_mount_args(
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=True,
                    sync_fw=False,
                ),
            ]
        )

        base_path = "/path/to/"
        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_to3 = "/path/to/path3"
        path_to4 = "/path/to/path4"
        path_from1 = os.path.join(claim_store.store_path, "path1")
        path_from2 = os.path.join(claim_store.store_path, "path2")
        path_from3 = os.path.join(claim_store.store_path, "path3")
        path_from4 = os.path.join(claim_store.store_path, "path4")
        assert get_volume_args(
            claim_store,
            "/path/to",
            artifacts=V1ArtifactsType(dirs=["path1", "path2"]),
            paths=["path3", "path4"],
        ) == " ".join(
            [
                get_or_create_args(path=path_to1),
                cp_mount_args(
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=False,
                    sync_fw=False,
                ),
                get_or_create_args(path=path_to2),
                cp_mount_args(
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=False,
                    sync_fw=False,
                ),
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend=V1ConnectionKind.VOLUME_CLAIM,
                    connection=claim_store.name,
                    path_from=path_from3,
                    path_to=path_to3,
                    is_file=False,
                    sync_fw=False,
                    check_path=True,
                ),
                get_or_create_args(path=base_path),
                cp_store_args(
                    backend=V1ConnectionKind.VOLUME_CLAIM,
                    connection=claim_store.name,
                    path_from=path_from4,
                    path_to=path_to4,
                    is_file=False,
                    sync_fw=False,
                    check_path=True,
                ),
            ]
        )

    def test_get_volume_args_host(self):
        host_path_store = V1Connection(
            name="test_path",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
        )
        path_to = "/path/to/"
        path_from = os.path.join(host_path_store.store_path, "")
        assert get_volume_args(host_path_store, path_to, None, None) == " ".join(
            [
                get_or_create_args(path=path_to),
                cp_mount_args(
                    path_from=path_from,
                    path_to=path_to,
                    is_file=False,
                    sync_fw=False,
                ),
            ]
        )

        host_path_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
        )
        path_to1 = "/path/to/path1"
        path_to2 = "/path/to/path2"
        path_from1 = os.path.join(host_path_store.store_path, "path1")
        path_from2 = os.path.join(host_path_store.store_path, "path2")
        assert get_volume_args(
            host_path_store,
            "/path/to",
            artifacts=V1ArtifactsType(dirs=["path1", "path2"]),
            paths=None,
        ) == " ".join(
            [
                get_or_create_args(path=path_to1),
                cp_mount_args(
                    path_from=path_from1,
                    path_to=path_to1,
                    is_file=False,
                    sync_fw=False,
                ),
                get_or_create_args(path=path_to2),
                cp_mount_args(
                    path_from=path_from2,
                    path_to=path_to2,
                    is_file=False,
                    sync_fw=False,
                ),
            ]
        )

    def test_get_artifacts_store_args(self):
        assert get_artifacts_store_args(artifacts_path="/some/path", clean=True) == (
            'if [ ! -d "/some/path" ]; then mkdir -m 0777 -p /some/path; fi; '
            'if [ -d /some/path ] && [ "$(ls -A /some/path)" ]; '
            "then rm -R /some/path/*; fi;"
        )

    def test_get_repo_context_args_requires_from_image(self):
        with self.assertRaises(PolyaxonConverterError):
            get_repo_context_args(name=None, url=None, revision=None, mount_path=None)

    def test_get_repo_context_args_with_none_values(self):
        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision=None,
            mount_path="/somepath",
        )
        assert args == ["--repo-path=/somepath/user/repo1", "--url=http://foo.com"]

    def test_get_repo_context_args(self):
        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision="00b9d2ea01c40f58d6b4051319f9375675a43c02",
            mount_path="/somepath",
        )
        assert args == [
            "--repo-path=/somepath/user/repo1",
            "--url=http://foo.com",
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
        ]

        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision="dev",
            mount_path="/somepath",
        )
        assert args == [
            "--repo-path=/somepath/user/repo1",
            "--url=http://foo.com",
            "--revision=dev",
        ]

        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision="00b9d2ea01c40f58d6b4051319f9375675a43c02",
            mount_path="/somepath",
        )
        assert args == [
            "--repo-path=/somepath/user/repo1",
            "--url=http://foo.com",
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
        ]
