import os

from clipped.utils.http import clean_host

from polyaxon.api import LOCALHOST
from polyaxon.env_vars.keys import EV_KEYS_PLATFORM_HOST


def get_api_host(default: str = LOCALHOST):
    return clean_host(os.environ.get(EV_KEYS_PLATFORM_HOST, default))
