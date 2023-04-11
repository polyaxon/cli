#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from clipped.dict_utils import dict_to_tabulate
from clipped.formatting import Printer
from clipped.json_utils import orjson_dumps


def get_entity_details(entity: any, entity_name: str):
    if entity.description:
        Printer.heading("{} description:".format(entity_name))
        Printer.print("{}\n".format(entity.description))

    if entity.settings:
        Printer.heading("{} settings:".format(entity_name))
        Printer.print(
            "{}\n".format(
                entity.settings.to_dict()
                if hasattr(entity.settings, "to_dict")
                else entity.settings
            )
        )

    if entity.readme:
        Printer.heading("{} readme:".format(entity_name))
        Printer.print_md(entity.readme)

    response = dict_to_tabulate(
        entity.to_dict(),
        humanize_values=True,
        exclude_attrs=["description", "settings", "readme"],
    )

    Printer.heading("{} info:".format(entity_name))
    Printer.dict_tabulate(response)


def handle_output(response: any, output: str):
    if output == "json":
        Printer.pprint(response)
        return
    if "path=" in output:
        json_path = output.strip("path=")
        with open(json_path, "w", encoding="utf8", newline="") as output_file:
            output_file.write(orjson_dumps(response))
