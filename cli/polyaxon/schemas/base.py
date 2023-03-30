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
import functools
import os
import pprint

from collections.abc import Mapping
from datetime import timezone
from typing import Any, Callable

import ujson

from pydantic import BaseModel, Extra

from polyaxon import pkg
from polyaxon.config_reader.spec import ConfigSpec
from polyaxon.exceptions import PolyaxonSchemaError
from polyaxon.schemas.patch_strategy import V1PatchStrategy
from polyaxon.utils.dict_utils import deep_update
from polyaxon.utils.humanize import humanize_timesince
from polyaxon.utils.string_utils import to_camel_case
from polyaxon.utils.tz_utils import get_timezone
from traceml.processors.units_processors import to_percentage, to_unit_memory


class BaseMetaConfig:
    allow_population_by_field_name = True
    validate_assignment = True
    arbitrary_types_allowed = True
    extra = Extra.forbid


class BaseSchemaModel(BaseModel):
    _IDENTIFIER = None
    _DEFAULT_INCLUDE_ATTRIBUTES = []
    _DEFAULT_EXCLUDE_ATTRIBUTES = []
    _DATETIME_ATTRIBUTES = []
    _MEM_SIZE_ATTRIBUTES = []
    _PERCENT_ATTRIBUTES = []
    _ROUNDING = 2
    _WRITE_MODE = 0o777
    _FIELDS_MANUAL_PATCH = []
    _FIELDS_SAME_KIND_PATCH = []
    _SWAGGER_FIELDS = []
    _SWAGGER_FIELDS_LISTS = ["tolerations"]
    _PARTIAL = False

    @classmethod
    def get_identifier(cls):
        return cls._IDENTIFIER

    @staticmethod
    def _dump(obj_dict):
        return ujson.dumps(obj_dict)

    def to_light_dict(
        self,
        humanize_values=False,
        include_attrs=None,
        exclude_attrs=None,
        dump=False,
    ):
        obj_dict = self.to_dict(humanize_values=humanize_values)
        if all([include_attrs, exclude_attrs]):
            raise PolyaxonSchemaError(
                "Only one value `include_attrs` or `exclude_attrs` is allowed."
            )
        if not any([include_attrs, exclude_attrs]):  # Use Default setup attrs
            include_attrs = self._DEFAULT_INCLUDE_ATTRIBUTES
            exclude_attrs = self._DEFAULT_EXCLUDE_ATTRIBUTES

        if include_attrs:
            exclude_attrs = set(obj_dict.keys()) - set(include_attrs)
        for attr in exclude_attrs:
            obj_dict.pop(attr, None)

        if dump:
            return self._dump(obj_dict)
        return obj_dict

    def to_dict(
        self,
        humanize_values=False,
        dump=False,
        include_kind=False,
        include_version=False,
        exclude_unset=True,
        exclude_none=True,
        exclude_defaults=False,
    ):
        obj = self.obj_to_dict(
            self,
            humanize_values=humanize_values,
            include_kind=include_kind,
            include_version=include_version,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        if dump:
            return self._dump(obj)
        return obj

    def to_json(
        self,
        humanize_values=False,
        include_kind=False,
        include_version=False,
    ):
        if include_kind and "kind" in self.__fields__.keys():
            self.kind = self._IDENTIFIER

        if include_version and "version" in self.__fields__.keys():
            self.version = pkg.SCHEMA_VERSION
        return self.obj_to_json(
            self,
            humanize_values=humanize_values,
        )

    def to_str(self) -> str:
        return pprint.pformat(self.dict(by_alias=True))

    def to_schema(self):
        return self.obj_to_schema(self)

    @classmethod
    def humanize_attrs(cls, obj):
        humanized_attrs = {}
        for attr in cls._DATETIME_ATTRIBUTES:
            humanized_attrs[attr] = humanize_timesince(getattr(obj, attr))
        for attr in cls._PERCENT_ATTRIBUTES:
            humanized_attrs[attr] = to_percentage(getattr(obj, attr), cls._ROUNDING)
        for attr in cls._MEM_SIZE_ATTRIBUTES:
            humanized_attrs[attr] = to_unit_memory(getattr(obj, attr))
        return humanized_attrs

    @classmethod
    def obj_to_json(
        cls,
        obj,
        humanize_values=False,
        exclude_unset=True,
        exclude_none=True,
        exclude_defaults=False,
    ):
        return obj.json(
            by_alias=True,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @staticmethod
    def swagger_to_dict(fdata: Any):
        def _field_to_dict(fvalue: Any):
            if hasattr(fvalue, "to_dict"):
                fvalue = fvalue.to_dict()
                keys = set(fvalue.keys())
                for k in keys:
                    if fvalue[k] is None:
                        del fvalue[k]
                return {to_camel_case(k): fvalue[k] for k in fvalue}
            return fvalue

        if not fdata:
            return fdata
        elif fdata and isinstance(fdata, list):
            return [_field_to_dict(v) for v in fdata]
        else:
            return _field_to_dict(fdata)

    def dict(self, *args, **kwargs) -> "DictStrAny":
        data = super().dict(*args, **kwargs)
        # Handle swagger fields and perform `to_dict`
        for field in self._SWAGGER_FIELDS:
            if field in data:
                data[field] = self.swagger_to_dict(data[field])
        return data

    @classmethod
    def obj_to_dict(
        cls,
        obj,
        humanize_values=False,
        include_kind=False,
        include_version=False,
        exclude_unset=True,
        exclude_none=True,
        exclude_defaults=False,
    ):
        humanized_attrs = cls.humanize_attrs(obj) if humanize_values else {}
        data_dict = obj.dict(
            by_alias=True,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

        if include_kind and "kind" not in data_dict and hasattr(obj, "kind"):
            data_dict["kind"] = obj._IDENTIFIER

        if include_version and "version" not in data_dict:
            data_dict["version"] = pkg.SCHEMA_VERSION

        for k, v in humanized_attrs.items():
            data_dict[k] = v
        return data_dict

    @classmethod
    def obj_to_schema(cls, obj):
        return {cls._IDENTIFIER: cls.obj_to_dict(obj)}

    @classmethod
    def from_dict(cls, value, partial: bool = False):
        return cls.parse_obj(value)

    @classmethod
    def read(cls, values, partial: bool = False, config_type=None):
        values = ConfigSpec.read_from(values, config_type=config_type)
        return cls.from_dict(values, partial=partial)

    @classmethod
    def init_file(cls, filepath: str, config=None):
        if not os.path.exists(filepath):
            cls.write(config or cls(), filepath=filepath, mode=cls._WRITE_MODE)

    def write(self, filepath: str, mode: int = None):
        with open(filepath, "w") as config_file:
            config_file.write(self.to_json())
            if mode is not None:
                os.chmod(filepath, mode)

    def clone(self):
        return self.from_dict(self.to_dict())

    @staticmethod
    def patch_normal_merge(current_value, value, strategy: V1PatchStrategy = None):
        strategy = strategy or V1PatchStrategy.POST_MERGE

        if isinstance(current_value, Mapping):
            if V1PatchStrategy.is_post_merge(strategy):
                return deep_update(current_value, value)
            elif V1PatchStrategy.is_pre_merge(strategy):
                return deep_update(value, current_value)
        elif isinstance(current_value, list):
            if V1PatchStrategy.is_post_merge(strategy):
                return current_value + [i for i in value if i not in current_value]
            elif V1PatchStrategy.is_pre_merge(strategy):
                return value + [i for i in current_value if i not in value]
        elif isinstance(current_value, BaseSchemaModel):
            return current_value.patch(value, strategy=strategy)
        elif hasattr(current_value, "to_dict"):
            if V1PatchStrategy.is_post_merge(strategy):
                return deep_update(current_value.to_dict(), value.to_dict())
            elif V1PatchStrategy.is_pre_merge(strategy):
                return deep_update(value.to_dict(), current_value.to_dict())
        else:
            if V1PatchStrategy.is_post_merge(strategy):
                return value
            elif V1PatchStrategy.is_pre_merge(strategy):
                return current_value

    @classmethod
    def patch_swagger_field(cls, config, values, strategy: V1PatchStrategy = None):
        strategy = strategy or V1PatchStrategy.POST_MERGE

        openapi_types = getattr(config, "openapi_types", {})
        for key in openapi_types:
            value = getattr(values, key, None)
            if value is None:
                continue

            current_value = getattr(config, key, None)
            if current_value is None:
                setattr(
                    config, key, value
                )  # handles also V1PatchStrategy.ISNULL implicitly
                continue

            if V1PatchStrategy.is_null(strategy):
                continue
            if V1PatchStrategy.is_replace(strategy):
                setattr(config, key, value)
                continue

            setattr(config, key, cls.patch_normal_merge(current_value, value, strategy))

    @classmethod
    def patch_swagger_field_list(
        cls, current_value, value, strategy: V1PatchStrategy = None
    ):
        strategy = strategy or V1PatchStrategy.POST_MERGE

        if V1PatchStrategy.is_null(strategy):
            return current_value
        if V1PatchStrategy.is_replace(strategy):
            return value

        return cls.patch_normal_merge(current_value, value, strategy)

    @classmethod
    def patch_obj(cls, config, values, strategy: V1PatchStrategy = None):
        strategy = strategy or V1PatchStrategy.POST_MERGE

        for key in config.__fields__.keys():
            if key in cls._FIELDS_MANUAL_PATCH:
                continue

            value = getattr(values, key, None)
            if value is None:
                should_continue = True
                if isinstance(values, Mapping) and key in values:
                    should_continue = False
                elif (
                    isinstance(values, BaseSchemaModel) and key in values.__fields_set__
                ):
                    should_continue = False

                if should_continue:
                    continue

            current_value = getattr(config, key, None)
            if current_value is None:
                setattr(
                    config, key, value
                )  # handles also V1PatchStrategy.ISNULL implicitly
                continue

            if (
                isinstance(current_value, BaseSchemaModel)
                and key not in cls._FIELDS_SAME_KIND_PATCH
            ):
                current_value.patch(value, strategy=strategy)
                continue

            if not isinstance(current_value, BaseSchemaModel) and (
                hasattr(current_value, "openapi_types") or key in cls._SWAGGER_FIELDS
            ):
                if key in cls._SWAGGER_FIELDS_LISTS:  # Special case for lists
                    setattr(
                        config,
                        key,
                        cls.patch_swagger_field_list(current_value, value, strategy),
                    )
                else:
                    cls.patch_swagger_field(current_value, value, strategy)
                continue

            if V1PatchStrategy.is_null(strategy):
                continue
            if V1PatchStrategy.is_replace(strategy):
                setattr(config, key, value)
                continue

            # We only handle merge strategies
            def normal_merge():
                setattr(
                    config, key, cls.patch_normal_merge(current_value, value, strategy)
                )

            def same_kind_merge():
                # If the same kind resume merge patch using base logic
                if value and current_value.kind == value.kind:
                    normal_merge()
                # Not same kind use post/pre replace
                else:
                    if V1PatchStrategy.is_post_merge(strategy):
                        setattr(config, key, value)
                    elif V1PatchStrategy.is_pre_merge(strategy):
                        setattr(config, key, current_value)

            if key in cls._FIELDS_SAME_KIND_PATCH or value is None:
                same_kind_merge()
            else:
                normal_merge()

        return config

    def patch(self, values, strategy: V1PatchStrategy = None):
        strategy = strategy or V1PatchStrategy.POST_MERGE
        return self.patch_obj(self, values, strategy)

    @staticmethod
    def localize_date(dt):
        if not dt:
            return dt
        if not dt.tzinfo:
            dt = timezone.utc.localize(dt)
        return dt.astimezone(get_timezone())

    @staticmethod
    def _get_bool(value, default_value):
        if isinstance(value, bool):
            return value

        return default_value

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True
        arbitrary_types_allowed = True
        use_enum_values = True
        extra = Extra.forbid
        json_dumps: Callable[..., str] = ujson.dumps
        json_loads = ujson.loads


def to_partial(cls):
    class NewCls(cls):
        _PARTIAL = True

    NewCls.__name__ = f"Partial{cls.__name__}"

    for field in NewCls.__fields__.values():
        if hasattr(field.type_, "__base__") and issubclass(
            field.type_.__base__, BaseModel
        ):
            field.type_ = to_partial(field.type_)

    return NewCls


def skip_partial(f):
    """
    `skip_partial` is a decorator to skip validation when `_PARTIAL = True` and return the data as is.

    usage example:
        @root_validator
        @skip_partial
        def my_custom_check(cls, values):
            ...
            return ...
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        cls_arg = None
        v_args = None
        if args:
            cls_arg = args[0]
            if len(args) > 1:
                v_args = args[1]
        partial_property = getattr(cls_arg, f"_PARTIAL", None)
        if partial_property:
            return v_args
        return f(*args, **kwargs)

    return wrapper


class BaseDiscriminatedModel(BaseSchemaModel):
    def __init__(self, **data):
        data["kind"] = data.pop("kind", self._IDENTIFIER)
        super().__init__(**data)


NAME_REGEX = r"^[-a-zA-Z0-9_]+\Z"
FULLY_QUALIFIED_NAME_REGEX = r"^[-a-zA-Z0-9_]+(:[-a-zA-Z0-9_.]+)?\Z"
