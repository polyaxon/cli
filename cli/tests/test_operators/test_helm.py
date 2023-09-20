import mock
import pytest

from polyaxon._deploy.operators.helm import HelmOperator
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonOperatorException

DUMMY_RETURN_VALUE = object()


@pytest.mark.operators_mark
class TestHelmOperator(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.helm = HelmOperator()

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
    def test_helm(self, mock_subprocess):
        mock_subprocess.Popen = self.mock_popen(0, "bar")
        assert self.helm.execute(["foo"]) == "bar"
        assert mock_subprocess.Popen.call_args[0][0] == ["helm", "foo"]

    @mock.patch("polyaxon._deploy.operators.cmd_operator.subprocess")
    def test_helm_error(self, mock_subprocess):
        return_code = 1
        stdout = "output"
        stderr = "error"
        mock_subprocess.Popen = self.mock_popen(return_code, stdout, stderr)
        with self.assertRaises(PolyaxonOperatorException) as exception:
            self.helm.execute(["foo"])
        assert exception.exception.message == (
            "`helm` command ('helm', 'foo') failed with exit status "
            "{}\nstdout:\n{}\nstderr:\n{}".format(return_code, stdout, stderr)
        )
