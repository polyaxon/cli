from typing import Dict, Optional

from clipped.utils.dates import to_timestamp
from clipped.utils.enums import get_enum_value
from clipped.utils.http import absolute_uri, add_notification_referrer_param
from vents.notifiers import NotificationSpec as _NotificationSpec

from polyaxon import settings
from polyaxon._connections import CONNECTION_CONFIG
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._schemas.lifecycle import StatusColor, V1StatusCondition
from polyaxon._utils.urls_utils import get_run_url


class NotificationSpec(_NotificationSpec, BaseSchemaModel):
    @staticmethod
    def load_from_data(
        kind: str,
        owner: str,
        project: str,
        uuid: str,
        name: str,
        status: str,
        wait_time: str,
        duration: str,
        condition: V1StatusCondition,
        inputs: Dict,
        outputs: Dict,
    ) -> "NotificationSpec":
        def get_details() -> str:
            details = "{} ({})".format(name, uuid) if name else uuid
            details = "Run: {}\n".format(details)
            if kind:
                details = "Kind: `{}`\n".format(get_enum_value(kind))
            details += "Status: `{}`\n".format(status)
            if condition.reason:
                details += "Reason: `{}`\n".format(condition.reason)
            if condition.message:
                details += "Message: `{}`\n".format(condition.message)
            details += "Transition time: `{}`\n".format(condition.last_transition_time)
            if wait_time:
                details += "Wait time: `{}`\n".format(wait_time)
            if duration:
                details += "Duration: `{}`\n".format(duration)
            if inputs:
                details += "Inputs: `{}`\n".format(inputs)
            if outputs:
                details += "Outputs: `{}`\n".format(outputs)

            return details

        def get_title() -> str:
            title = "{} ({})".format(name, uuid) if name else uuid
            title += " Status: {}\n".format(status)
            return title

        def get_color() -> str:
            return StatusColor.get_color(condition.type)

        def get_url() -> Optional[str]:
            if not (owner and project and uuid):
                return
            uri = get_run_url(owner=owner, project_name=project, run_uuid=uuid)
            uri = "ui{}".format(uri)
            url = absolute_uri(host=settings.CLIENT_CONFIG.host, url=uri)
            url = add_notification_referrer_param(
                url,
                provider=CONNECTION_CONFIG.project_name,
                is_absolute=False,
            )
            return url

        return NotificationSpec(
            context={
                "owner": owner,
                "project": project,
                "uuid": uuid,
                "name": name,
            },
            fallback=condition.type,
            title=get_title(),
            details=get_details(),
            description=condition.reason,
            url=get_url(),
            color=get_color(),
            ts=to_timestamp(condition.last_transition_time),
        )
