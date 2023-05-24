import json
import subprocess

from tempfile import TemporaryFile

from polyaxon.exceptions import PolyaxonOperatorException


class CmdOperator:
    CMD = ""

    @classmethod
    def _execute(
        cls,
        params,
        env,
        is_json: bool = False,
        stream: bool = False,
        output_only: bool = True,
    ):
        def _stream():
            with TemporaryFile("w+") as stderr:
                ps = subprocess.Popen(params, env=env, stderr=stderr)
                exit_status = ps.wait()
                stderr.seek(0)
                if exit_status != 0:
                    raise PolyaxonOperatorException(
                        cmd=cls.CMD,
                        args=params,
                        return_code=exit_status,
                        stdout=None,
                        stderr=stderr,
                    )

        def _block():
            with TemporaryFile("w+") as stdout, TemporaryFile("w+") as stderr:
                ps = subprocess.Popen(params, env=env, stdout=stdout, stderr=stderr)
                exit_status = ps.wait()
                stdout.seek(0)
                stderr.seek(0)
                if exit_status != 0:
                    raise PolyaxonOperatorException(
                        cmd=cls.CMD,
                        args=params,
                        return_code=exit_status,
                        stdout=stdout,
                        stderr=stderr,
                    )

                return json.load(stdout) if is_json else stdout.read()

        if output_only:
            return _stream() if stream else _block()

        return subprocess.Popen(params, env=env, stdout=subprocess.PIPE)

    @classmethod
    def check(cls):
        return True
