from clipped.formatting import Printer
from clipped.utils.dicts import dict_to_tabulate
from clipped.utils.json import orjson_dumps


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
