import pytest

from clipped.types.docker_image import validate_image

from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.polyflow_mark
class TestImageValidation(BaseTestCase):
    def test_valid_image(self):
        assert validate_image(None, allow_none=True) is None
        assert validate_image("", allow_none=True) is None

        with self.assertRaises(ValueError):
            validate_image("some_image_name:sdf:sdf:foo")

        with self.assertRaises(ValueError):
            validate_image("registry.foobar.com/my/docker/some_image_name:foo:foo")

        with self.assertRaises(ValueError):
            validate_image("some_image_name / foo")

        with self.assertRaises(ValueError):
            validate_image("some_image_name /foo:sdf")

        with self.assertRaises(ValueError):
            validate_image("some_image_name /foo :sdf")

        with self.assertRaises(ValueError):
            validate_image("registry.foobar.com:foo:foo/my/docker/some_image_name:foo")

        with self.assertRaises(ValueError):
            validate_image("registry.foobar.com:foo:foo/my/docker/some_image_name")

        with self.assertRaises(ValueError):
            validate_image("registry.foobar.com:/my/docker/some_image_name:foo")
