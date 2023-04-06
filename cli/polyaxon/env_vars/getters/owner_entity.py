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

import sys

from clipped.formatting import Printer
from clipped.string_utils import validate_slug

from polyaxon.constants.globals import DEFAULT
from polyaxon.env_vars.getters.user import get_local_owner
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError
from polyaxon.utils.fqn_utils import get_entity_info


def resolve_entity_info(entity: str, entity_name: str, is_cli: bool = False):
    from polyaxon import settings

    if not entity:
        message = "Please provide a valid {}!".format(entity_name)
        if is_cli:
            Printer.error(message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(message)

    owner, entity_value = get_entity_info(entity)

    if not owner:
        owner = get_local_owner(is_cli=is_cli)

    if not owner and (not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community):
        owner = DEFAULT

    if not owner:
        owner = settings.AUTH_CONFIG.username if settings.AUTH_CONFIG else None

    if not all([owner, entity_value]):
        message = "Please provide a valid {}.".format(entity_name)
        if is_cli:
            Printer.error(message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(message)
    if owner and not validate_slug(owner):
        raise PolyaxonSchemaError(
            "Received an invalid owner, received the value: `{}`".format(owner)
        )

    if entity_value and not validate_slug(entity_value):
        raise PolyaxonSchemaError(
            "Received an invalid {}, received the value: `{}`".format(
                entity_name, entity_value
            )
        )
    return owner, entity_value
