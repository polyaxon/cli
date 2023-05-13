import sys

from typing import List

from clipped.formatting import Printer

from polyaxon import settings
from polyaxon.cli.errors import handle_cli_error
from polyaxon.cli.operations import logs as run_logs
from polyaxon.exceptions import (
    PolyaxonCompilerError,
    PolyaxonConverterError,
    PolyaxonK8sError,
)
from polyaxon.k8s import converter
from polyaxon.k8s.executor.executor import Executor
from polyaxon.polyaxonfile.specs import OperationSpecification
from polyaxon.polyflow import V1Operation
from polyaxon.utils.fqn_utils import get_resource_name


def run(
    ctx,
    name: str,
    owner: str,
    project_name: str,
    description: str,
    tags: List[str],
    op_spec: V1Operation,
    log: bool,
):
    if not settings.SET_AGENT:
        Printer.warning("Agent not configured!")
        return

    def create_run():
        Printer.print("Creating a run.")
        try:
            compiled_operation = OperationSpecification.compile_operation(op_spec)
            run_name = compiled_operation.name or name
            resource = converter.make(
                owner_name=owner,
                project_name=project_name,
                project_uuid=project_name,
                run_uuid=run_name,
                run_name=name,
                run_path=run_name,
                compiled_operation=compiled_operation,
                params=op_spec.params,
                default_sa=settings.AGENT_CONFIG.runs_sa,
            )
            Executor(namespace=settings.AGENT_CONFIG.namespace).create(
                run_uuid=run_name,
                run_kind=compiled_operation.get_run_kind(),
                resource=resource,
            )
            # cache.cache(config_manager=RunConfigManager, response=response)
            run_job_uid = get_resource_name(run_name)
            Printer.success("A new run `{}` was created".format(run_job_uid))
        except (PolyaxonCompilerError, PolyaxonK8sError, PolyaxonConverterError) as e:
            handle_cli_error(e, message="Could not create a run.")
            sys.exit(1)

    create_run()
    logs_cmd = run_logs

    # Check if we need to invoke logs
    if log and logs_cmd:
        ctx.obj = {"project": "{}/{}".format(owner, project_name)}
        ctx.invoke(logs_cmd)
