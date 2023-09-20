from typing import List

from polyaxon._contexts import paths as ctx_paths


def get_artifacts_store_args(artifacts_path: str, clean: bool) -> str:
    get_or_create = 'if [ ! -d "{dir}" ]; then mkdir -m 0777 -p {dir}; fi;'.format(
        dir=artifacts_path
    )
    delete_dir = (
        'if [ -d {path} ] && [ "$(ls -A {path})" ]; '
        "then rm -R {path}/*; fi;".format(path=artifacts_path)
    )
    if clean:
        return "{} {}".format(get_or_create, delete_dir)
    return "{}".format(get_or_create)


def init_artifact_context_args(run_path: str) -> List[str]:
    return [
        'if [ ! -d "{dir}" ]; then mkdir -m 0777 -p {dir}; fi;'.format(
            dir=ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_path)
        ),
        'if [ ! -d "{dir}" ]; then mkdir -m 0777 -p {dir}; fi;'.format(
            dir=ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_path) + "/outputs"
        ),
    ]
