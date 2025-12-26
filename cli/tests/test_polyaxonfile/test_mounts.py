import pytest
from polyaxon._flow import V1Operation, V1RunKind
from polyaxon._schemas.types.mounts import V1Mount
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.polyaxonfile_mark
class TestMounts(BaseTestCase):
    def test_mount_short_syntax(self):
        config_dict = {
            "version": 1.1,
            "kind": "operation",
            "mount": ["./src:/dst", "./src2"],
            "component": {
                "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}}
            },
        }
        op_config = V1Operation.read(values=config_dict)
        assert op_config.mount == ["./src:/dst", "./src2"]
        assert op_config.get_resolved_mount() == [
            V1Mount(path_from="./src", path_to="/dst"),
            V1Mount(path_from="./src2", path_to=None),
        ]

    def test_mount_long_syntax(self):
        config_dict = {
            "version": 1.1,
            "kind": "operation",
            "mount": [
                {"from": "./src", "to": "/dst"},
                {"from": "./src2"},
                {"to": "/dst2"},
            ],
            "component": {
                "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}}
            },
        }
        op_config = V1Operation.read(values=config_dict)
        assert len(op_config.mount) == 3
        assert isinstance(op_config.mount[0], V1Mount)
        assert op_config.mount[0].path_from == "./src"
        assert op_config.mount[0].path_to == "/dst"
        assert op_config.mount[1].path_from == "./src2"
        assert op_config.mount[1].path_to is None
        assert op_config.mount[2].path_from is None
        assert op_config.mount[2].path_to == "/dst2"
        assert op_config.get_resolved_mount() == [
            V1Mount(path_from="./src", path_to="/dst"),
            V1Mount(path_from="./src2", path_to=None),
            V1Mount(path_from=None, path_to="/dst2"),
        ]
