import inspect
import pytest
import warnings

import click
from click.testing import CliRunner

from polyaxon._cli.utils import write_stream
from polyaxon._utils.test_utils import BaseTestCase


LINE = "\x1b[31mred\x1b[0m café\n"


@click.command()
@click.argument("kind")
@click.option("--err", is_flag=True)
def write(kind, err):
    write_stream(LINE.encode() if kind == "bytes" else LINE, err=err)


def _cli_runner_with_stderr():
    if "mix_stderr" in inspect.signature(CliRunner.__init__).parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()


@pytest.mark.cli_mark
class TestWriteStream(BaseTestCase):
    def test_writes_text_and_bytes_unchanged_without_deprecations(self):
        for kind in ("text", "bytes"):
            for err in (False, True):
                with self.subTest(kind=kind, err=err), warnings.catch_warnings():
                    warnings.simplefilter("error", DeprecationWarning)
                    result = _cli_runner_with_stderr().invoke(
                        write, [kind, "--err"] if err else [kind]
                    )

                    assert result.exception is None, repr(result.exception)
                    assert result.stdout == ("" if err else LINE)
                    assert result.stderr == (LINE if err else "")
