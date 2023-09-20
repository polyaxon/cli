import mock
import pytest

from polyaxon._deploy.operators.pip import PipOperator
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonOperatorException

DUMMY_RETURN_VALUE = object()


@pytest.mark.operators_mark
class TestPipOperator(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.pip = PipOperator()

    @staticmethod
    def mock_popen(return_code, out_msg, err_msg=None):
        def popen(*args, **kwargs):
            stdout = kwargs.pop("stdout")
            stdout.write(out_msg)
            if err_msg:
                stderr = kwargs.pop("stderr")
                stderr.write(err_msg)
            return mock.Mock(wait=mock.Mock(return_value=return_code))

        return mock.Mock(side_effect=popen)

    @mock.patch("polyaxon._deploy.operators.cmd_operator.subprocess")
    def test_pip(self, mock_subprocess):
        mock_subprocess.Popen = self.mock_popen(0, "bar")
        assert self.pip.execute(["install"]) == "bar"
        assert mock_subprocess.Popen.call_args[0][0] == ["pip", "install"]

    @mock.patch("polyaxon._deploy.operators.cmd_operator.subprocess")
    def test_pip_error(self, mock_subprocess):
        return_code = 1
        stdout = "output"
        stderr = "error"
        mock_subprocess.Popen = self.mock_popen(return_code, stdout, stderr)
        with self.assertRaises(PolyaxonOperatorException) as exception:
            self.pip.execute(["run"])

        self.assertEqual(
            exception.exception.message,
            "`pip` command ('pip', 'run') "
            "failed with exit status {}\nstdout:\n{}\nstderr:\n{}".format(
                return_code, stdout, stderr
            ),
        )
