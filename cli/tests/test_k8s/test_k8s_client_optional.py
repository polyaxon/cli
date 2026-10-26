import pytest
import subprocess
import sys
from textwrap import dedent

from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestK8sClientOptional(BaseTestCase):
    def run_code(self, code):
        return subprocess.run(
            [sys.executable, "-c", dedent(code)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_library_modules_do_not_load_the_client(self):
        output = self.run_code(
            """
            import sys

            import polyaxon.client
            import polyaxon.k8s
            import polyaxon.polyaxonfile
            import polyaxon.schemas

            modules = {m.split(".")[0] for m in sys.modules}
            print(sorted(modules & {"kubernetes", "kubernetes_asyncio"}))
            """
        )

        assert output == "[]"

    def test_modules_import_without_the_client(self):
        output = self.run_code(
            """
            import sys

            sys.modules["kubernetes"] = None
            sys.modules["kubernetes_asyncio"] = None

            from polyaxon import docker, k8s

            print(docker.Agent.__name__, k8s.V1Container.__name__)
            """
        )

        assert output == "Agent V1Container"
