import click

OPTIONS_OWNER = {
    "args": ["--owner", "-o"],
    "kwargs": dict(
        type=str,
        help="Name of the owner/namespace, "
        "if not provided it will default to the namespace of the current user.",
    ),
}

OPTIONS_NAME = {
    "args": ["--name", "-n"],
}

OPTIONS_PROJECT = {
    "args": ["--project", "-p"],
    "kwargs": dict(type=str, help="The project name, e.g. 'mnist' or 'acme/mnist'."),
}

OPTIONS_MODEL_VERSION = {
    "args": ["--version", "-ver"],
    "kwargs": dict(
        type=str,
        help="The component version, e.g. 'v1.3.4' or 'rc1' or 'latest'.",
    ),
}

OPTIONS_COMPONENT_VERSION = {
    "args": ["--version", "-ver"],
    "kwargs": dict(
        type=str,
        help="The component version, e.g. 'v1.3.4' or 'rc1' or 'latest'.",
    ),
}


OPTIONS_ARTIFACT_VERSION = {
    "args": ["--version", "-ver"],
    "kwargs": dict(
        type=str,
        help="The artifact version, e.g. 'v1.3.4' or 'rc1' or 'latest'.",
    ),
}

OPTIONS_RUN_UID = {
    "args": ["--uid", "-uid"],
    "kwargs": dict(type=str, help="The run uuid."),
}


OPTIONS_RUN_OFFLINE = {
    "args": ["--offline"],
    "kwargs": dict(
        is_flag=True,
        default=False,
        help="To use the offline store, for resolving runs, if it exists.",
    ),
}

OPTIONS_RUN_OFFLINE_PATH_FROM = {
    "args": [
        "--path",
        "--path-from",
    ],
    "kwargs": dict(
        type=click.Path(exists=False),
        help="Optional offline root path to use where runs are persisted, "
        "default value is taken from the env var: `POLYAXON_OFFLINE_ROOT`.",
    ),
}
OPTIONS_RUN_OFFLINE_PATH_TO = {
    "args": [
        "--path",
        "--path-to",
    ],
    "kwargs": dict(
        type=click.Path(exists=False),
        help="Optional offline root path to use where runs are persisted, "
        "default value is taken from the env var: `POLYAXON_OFFLINE_ROOT`.",
    ),
}
