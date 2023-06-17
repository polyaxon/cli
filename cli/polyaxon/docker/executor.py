import os
import signal
import subprocess

from typing import Dict, List

from polyaxon.deploy.operators.docker import DockerOperator
from polyaxon.docker import docker_types
from polyaxon.docker.converter.converters import CONVERTERS
from polyaxon.docker.converter.mixins import MIXIN_MAPPING
from polyaxon.exceptions import PolyaxonAgentError
from polyaxon.lifecycle import V1Statuses
from polyaxon.logger import logger
from polyaxon.runner.executor import BaseExecutor
from polyaxon.runner.kinds import RunnerKind


class Executor(BaseExecutor):
    MIXIN_MAPPING = MIXIN_MAPPING
    CONVERTERS = CONVERTERS
    RUNNER_KIND = RunnerKind.DOCKER

    def __init__(self):
        super().__init__()
        self._ops = {}

    def _get_manager(self):
        return DockerOperator()

    def _get_op_proc(self, run_uuid: str) -> List[subprocess.Popen]:
        return self._ops.get(run_uuid)

    def create(
        self,
        run_uuid: str,
        run_kind: str,
        resource: List[docker_types.V1Container],
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
                logger.info(f"[Executor] message")
            else:
                logger.warning(f"[Executor] message")
                return {
                    "status": V1Statuses.FAILED,
                    "tasks": self._ops[run_uuid],
                    "message": message,
                }
        return {"status": V1Statuses.SUCCEEDED, "tasks": self._ops[run_uuid]}

    def apply(self, run_uuid: str, run_kind: str, resource: Dict) -> Dict:
        raise PolyaxonAgentError(
            "Docker executor does not support apply method.\n"
            "Run: <kind: {}, uuid: {}>".format(run_kind, run_uuid)
        )

    def stop(self, run_uuid: str, run_kind: str):
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

    def clean(self, run_uuid: str, run_kind: str):
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

    def get(self, run_uuid: str, run_kind: str) -> V1Statuses:
        procs = self._get_op_proc(run_uuid)
        return self._get_task_status(procs[-1])
