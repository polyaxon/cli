import sys

from typing import Dict, List, Union

import click

from clipped.formatting import Printer
from clipped.utils.lists import to_list
from clipped.utils.units import to_percentage, to_unit_memory

from polyaxon._schemas.container_resources import ContainerResourcesConfig


def resources(jobs_resources: Union[List[Dict], Dict]):
    jobs_resources = to_list(jobs_resources)
    click.clear()
    table = Printer.get_table("Job", "Mem Usage / Total", "CPU% - CPUs")
    for job_resources in jobs_resources:
        job_resources = ContainerResourcesConfig.from_dict(job_resources)
        line = [
            job_resources.job_name,
            "{} / {}".format(
                to_unit_memory(job_resources.memory_used),
                to_unit_memory(job_resources.memory_limit),
            ),
            "{} - {}".format(
                to_percentage(job_resources.cpu_percentage / 100),
                job_resources.n_cpus,
            ),
        ]
        table.add_row(*line)
    Printer.print(table)
    sys.stdout.flush()


def gpu_resources(jobs_resources: Union[List[Dict], Dict]):
    # TODO: move resources and other common configs to clippy

    jobs_resources = to_list(jobs_resources)
    click.clear()
    table = Printer.get_table(
        "job_name",
        "name",
        "GPU Usage",
        "GPU Mem Usage / Total",
        "GPU Temperature",
        "Power Draw / Limit",
    )
    non_gpu_jobs = 0
    for job_resources in jobs_resources:
        job_resources = ContainerResourcesConfig.from_dict(job_resources)
        line = []
        if not job_resources.gpu_resources:
            non_gpu_jobs += 1
            continue
        for gpu_resources in job_resources.gpu_resources:
            line += [
                job_resources.job_name,
                gpu_resources.name,
                to_percentage(gpu_resources.utilization_gpu / 100),
                "{} / {}".format(
                    to_unit_memory(gpu_resources.memory_used),
                    to_unit_memory(gpu_resources.memory_total),
                ),
                gpu_resources.temperature_gpu,
                "{} / {}".format(gpu_resources.power_draw, gpu_resources.power_limit),
            ]
        table.add_row(*line)
    if non_gpu_jobs == len(jobs_resources):
        Printer.error(
            "No GPU job was found, please run `resources` command without `-g | --gpu` option."
        )
        exit(1)
    Printer.print(table)
    sys.stdout.flush()
