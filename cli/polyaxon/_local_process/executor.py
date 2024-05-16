import os
import signal
import subprocess

from typing import Dict, List

from polyaxon._deploy.operators.cmd_operator import CmdOperator
from polyaxon._deploy.operators.conda import CondaOperator
from polyaxon._local_process import process_types
from polyaxon._local_process.converter.converters import CONVERTERS
from polyaxon._local_process.converter.mixins import MIXIN_MAPPING
from polyaxon._runner.executor import BaseExecutor
from polyaxon._runner.kinds import RunnerKind
from polyaxon._schemas.lifecycle import V1Statuses
from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.logger import logger


class Executor(BaseExecutor):
    MIXIN_MAPPING = MIXIN_MAPPING
    CONVERTERS = CONVERTERS
    RUNNER_KIND = RunnerKind.PROCESS

    def __init__(self, conda_env: str = None, venv: str = None):
        super().__init__()
        self._ops = {}
        self._conda_env = conda_env
        self._venv = venv

    def _get_manager(self):
        if self._conda_env:
            return CondaOperator()
        return CmdOperator()

    def _check_conda(self):
        if not self.manager.check():
            raise logger.error("Conda is required to run this command.")

        envs = self.manager.execute(["env", "list", "--json"], is_json=True)
        env_names = [os.path.basename(env) for env in envs["envs"]]
        if self._conda_env not in env_names:
            raise logger.error(
                "Conda env `{}` is not installed.".format(self._conda_env),
                sys_exit=True,
            )

    def _run_in_conda(self, cmd_bash, cmd_args):
        cmd_args = ["source activate {}".format(self._conda_env)] + cmd_args
        subprocess.Popen(cmd_bash + [" && ".join(cmd_args)], close_fds=True)

    def _get_op_proc(self, run_uuid: str) -> List[subprocess.Popen]:
        return self._ops.get(run_uuid)

    def create(
        self,
        run_uuid: str,
        run_kind: str,
        resource: List[process_types.V1Container],
        namespace: str = None,
    ) -> Dict:
        logger.info(f"[Executor] Starting operation {run_uuid} {run_kind}.")
        self._ops[run_uuid] = []
        for task in resource:
            logger.info(
                f"[Executor] Starting task container {task.name} {task.image} ."
            )
            proc = self.manager.execute(
                task.get_cmd_args(), env=os.environ, output_only=False
            )
            self._ops[run_uuid].append(proc)
            proc.wait()
            task_status = self._get_task_status(proc)
            message = f"Task container {task.name} {task.image} with id {proc.pid} {task_status}"
            if task_status == V1Statuses.SUCCEEDED:
                logger.info(f"[Executor] {message}")
            else:
                logger.warning(f"[Executor] {message}")
                self._clean_temp_execution_path(run_uuid)
                return {
                    "status": V1Statuses.FAILED,
                    "tasks": self._ops[run_uuid],
                    "message": message,
                }
        self._clean_temp_execution_path(run_uuid)
        return {"status": V1Statuses.SUCCEEDED, "tasks": self._ops[run_uuid]}

    def apply(
        self, run_uuid: str, run_kind: str, resource: Dict, namespace: str = None
    ) -> Dict:
        raise PolyaxonAgentError(
            "Docker executor does not support apply method.\n"
            "Run: <kind: {}, uuid: {}>".format(run_kind, run_uuid)
        )

    def stop(self, run_uuid: str, run_kind: str, namespace: str = None):
        proc = self._get_op_proc(run_uuid)
        if proc.poll() is None:
            # Kill the process tree rooted at the child if it's the leader of its own process
            # group, otherwise just kill the child
            try:
                if proc.pid == os.getpgid(proc.pid):
                    os.killpg(proc.pid, signal.SIGTERM)
                else:
                    proc.terminate()
            except OSError:
                # The child process may have exited before we attempted to terminate it, so we
                # ignore OSErrors raised during child process termination
                _msg = f"Failed to terminate operation {run_kind} {run_uuid} child process PID {proc.pid}"
                logger.debug(_msg)
            proc.wait()

    def clean(self, run_uuid: str, run_kind: str, namespace: str = None):
        return self.apply(
            run_uuid=run_uuid,
            run_kind=run_kind,
            resource={"metadata": {"finalizers": None}},
        )

    def _get_task_status(self, proc) -> V1Statuses:
        exit_code = proc.poll()
        if exit_code is None:
            return V1Statuses.RUNNING
        if exit_code == 0:
            return V1Statuses.SUCCEEDED
        return V1Statuses.FAILED

    def get(self, run_uuid: str, run_kind: str, namespace: str = None) -> V1Statuses:
        procs = self._get_op_proc(run_uuid)
        return self._get_task_status(procs[-1])

    def list_ops(self, namespace: str = None):
        return []
