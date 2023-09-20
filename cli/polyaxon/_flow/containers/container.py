from clipped.utils.lists import to_list
from clipped.utils.strings import strip_spaces


def get_container_command_args(config):
    def sanitize_str(value):
        if not value:
            return
        value = strip_spaces(value=value, join=False)
        value = [c.strip().strip("\\") for c in value if (c and c != "\\")]
        value = [c for c in value if (c and c != "\\")]
        return " ".join(value)

    def sanitize(value):
        return (
            [sanitize_str(v) for v in value]
            if isinstance(value, list)
            else to_list(sanitize_str(value), check_none=True)
        )

    return to_list(config.command, check_none=True), sanitize(config.args)
