import os

from clipped.utils.http import clean_host

from polyaxon.api import LOCALHOST
from polyaxon.env_vars.keys import ENV_KEYS_PLATFORM_HOST


def get_api_host(default: str = LOCALHOST):
    return clean_host(os.environ.get(ENV_KEYS_PLATFORM_HOST, default))
