from clipped.utils.validation import validate_tags

from polyaxon._schemas.types import V1TensorboardType

TENSORBOARD_INIT_COMMAND = ["polyaxon", "initializer", "tensorboard"]


def get_tensorboard_args(
    tb_args: V1TensorboardType, context_from: str, context_to: str, connection_kind: str
):
    args = [
        "--context-from={}".format(context_from),
        "--context-to={}".format(context_to),
        "--connection-kind={}".format(connection_kind),
    ]
    if tb_args.port:
        args.append("--port={}".format(tb_args.port))
    if tb_args.uuids:
        uuids = validate_tags(tb_args.uuids, validate_yaml=True)
        args.append("--uuids={}".format(",".join(uuids)))
    if tb_args.use_names:
        args.append("--use-names")
    if tb_args.path_prefix:
        args.append("--path-prefix={}".format(tb_args.path_prefix)),
    if tb_args.plugins:
        plugins = validate_tags(tb_args.plugins, validate_yaml=True)
        args.append("--plugins={}".format(",".join(plugins)))

    return args
