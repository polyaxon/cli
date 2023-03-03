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

import os

from collections.abc import Mapping
from typing import Optional

import ujson

from polyaxon.contexts import paths as ctx_paths
from polyaxon.logger import logger
from polyaxon.schemas.base import BaseConfig
from polyaxon.utils.path_utils import check_or_create_path


class BaseConfigManager:
    """Base class for managing a configuration file."""

    VISIBILITY_GLOBAL = "global"
    VISIBILITY_LOCAL = "local"
    VISIBILITY_ALL = "all"

    VISIBILITY = None
    IN_POLYAXON_DIR = False
    CONFIG_PATH = None
    CONFIG_FILE_NAME = None
    CONFIG = None

    @classmethod
    def is_global(cls, visibility=None):
        visibility = visibility or cls.VISIBILITY
        return visibility == cls.VISIBILITY_GLOBAL

    @classmethod
    def is_local(cls, visibility=None):
        visibility = visibility or cls.VISIBILITY
        return visibility == cls.VISIBILITY_LOCAL

    @classmethod
    def is_all_visibility(cls, visibility=None):
        visibility = visibility or cls.VISIBILITY
        return visibility == cls.VISIBILITY_ALL

    @classmethod
    def get_visibility(cls):
        if cls.is_all_visibility():
            return (
                cls.VISIBILITY_LOCAL
                if cls.is_locally_initialized()
                else cls.VISIBILITY_GLOBAL
            )
        return cls.VISIBILITY

    @classmethod
    def set_config_path(cls, config_path):
        cls.CONFIG_PATH = config_path

    @staticmethod
    def _create_dir(config_file_path):
        try:
            check_or_create_path(config_file_path, is_dir=False)
        except OSError:
            # Except permission denied and potential race conditions
            # in multi-threaded environments.
            logger.error(
                "Could not create config context directory for file `%s`",
                config_file_path,
            )

    @staticmethod
    def _get_and_check_path(config_path: str) -> Optional[str]:
        if config_path and os.path.isfile(config_path):
            return config_path
        return None

    @classmethod
    def get_local_config_path(cls) -> str:
        # local to this directory
        base_path = os.path.join(".")
        if cls.IN_POLYAXON_DIR:
            # Add it to the current "./.polyaxon"
            base_path = os.path.join(base_path, ".polyaxon")
        config_path = os.path.join(base_path, cls.CONFIG_FILE_NAME)
        return config_path

    @classmethod
    def check_local_config_path(cls) -> Optional[str]:
        return cls._get_and_check_path(cls.get_local_config_path())

    @classmethod
    def get_global_config_path(cls) -> str:
        if cls.CONFIG_PATH:
            base_path = os.path.join(cls.CONFIG_PATH, ".polyaxon")
        else:
            base_path = ctx_paths.CONTEXT_USER_POLYAXON_PATH
        config_path = os.path.join(base_path, cls.CONFIG_FILE_NAME)
        return config_path

    @classmethod
    def check_global_config_path(cls) -> Optional[str]:
        return cls._get_and_check_path(cls.get_global_config_path())

    @classmethod
    def get_tmp_config_path(cls) -> str:
        base_path = ctx_paths.CONTEXT_TMP_POLYAXON_PATH
        config_path = os.path.join(base_path, cls.CONFIG_FILE_NAME)
        return config_path

    @classmethod
    def get_config_filepath(cls, create=True, visibility=None):
        config_path = None
        if cls.is_local(visibility):
            config_path = cls.get_local_config_path()
        elif cls.is_global(visibility):
            config_path = cls.get_global_config_path()
        elif cls.is_all_visibility(visibility):
            config_path = cls.check_local_config_path()
            if not config_path:
                config_path = cls.get_global_config_path()

        if create and config_path:
            cls._create_dir(config_path)
        return config_path

    @classmethod
    def init_config(cls, visibility=None):
        config = cls.get_config()
        cls.set_config(config, init=True, visibility=visibility)

    @classmethod
    def is_locally_initialized(cls):
        return cls.check_local_config_path()

    @classmethod
    def is_initialized(cls):
        return cls._get_and_check_path(cls.get_config_filepath(create=False))

    @classmethod
    def set_config(cls, config, init=False, visibility=None):
        config_filepath = cls.get_config_filepath(visibility=visibility)

        if os.path.isfile(config_filepath) and init:
            logger.debug(
                "%s file already present at %s\n", cls.CONFIG_FILE_NAME, config_filepath
            )
            return

        with open(config_filepath, "w") as config_file:
            if hasattr(config, "to_dict"):
                logger.debug(
                    "Setting %s in the file %s\n",
                    config.to_dict(),
                    cls.CONFIG_FILE_NAME,
                )
                config_file.write(ujson.dumps(config.to_dict()))
            elif isinstance(config, Mapping):
                config_file.write(ujson.dumps(config))
            else:
                logger.debug(
                    "Setting %s in the file %s\n", config, cls.CONFIG_FILE_NAME
                )
                config_file.write(config)

    @classmethod
    def get_config(cls, check: bool = True):
        if check and not cls.is_initialized():
            return None

        config_filepath = cls.get_config_filepath()
        logger.debug(
            "Reading config `%s` from path: %s\n", cls.__name__, config_filepath
        )
        return cls.read_from_path(config_filepath)

    @classmethod
    def read_from_path(cls, config_filepath: str):
        if issubclass(cls.CONFIG, BaseConfig):
            return cls.CONFIG.read(config_filepath)
        with open(config_filepath, "r") as config_file:
            config_str = config_file.read()
        return cls.CONFIG(**ujson.loads(config_str))

    @classmethod
    def get_config_or_default(cls):
        if not cls.is_initialized():
            return cls.CONFIG()  # pylint:disable=not-callable

        return cls.get_config(check=False)

    @classmethod
    def get_config_from_env(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def get_value(cls, key):
        config = cls.get_config()
        if config:
            if hasattr(config, key):
                return getattr(config, key)
            else:
                logger.warning("Config `%s` has no key `%s`", cls.CONFIG.__name__, key)

        return None

    @classmethod
    def purge(cls, visibility=None):
        def _purge():
            if config_filepath and os.path.isfile(config_filepath):
                os.remove(config_filepath)

        if cls.is_all_visibility():
            if visibility:
                config_filepath = cls.get_config_filepath(
                    create=False, visibility=visibility
                )
                _purge()
            else:
                config_filepath = cls.get_config_filepath(
                    create=False, visibility=cls.VISIBILITY_LOCAL
                )
                _purge()
                config_filepath = cls.get_config_filepath(
                    create=False, visibility=cls.VISIBILITY_GLOBAL
                )
                _purge()
        else:
            config_filepath = cls.get_config_filepath(create=False)
            _purge()
