from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._schemas.lifecycle import V1Statuses


class V1Notification(BaseSchemaModel):
    """You can configure Polyaxon to send notifications to users and systems
    about event changes in your runs.

    Notifications also allow you to build or set up integrations using webhooks.
    External systems can subscribe or provide handling for certain events.
    When one of those events is triggered, Polyaxon will send an HTTP request
    payload to the webhook's configured URL.

    Polyaxon can send notifications when a run reaches a final status:

     * succeeded
     * failed
     * stopped
     * done (any final state)

     Args:
         connections: List[str]
         trigger: str

    ## YAML usage

    ```yaml
    >>> notification:
    >>>   connections: [slack-connection, discord-connection]
    >>>   trigger: failed
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Statuses,  V1Notification
    >>> notification = V1Notification(
    >>>     connections=["slack-connection", "discord-connection"],
    >>>     trigger=V1Statuses.FAILED,
    >>> )
    ```

    ## Fields

    ### connections

    The connections to notify, these [connections](/docs/setup/connections/)
    must be configured at deployment time.

    ```yaml
    >>> notification:
    >>>   connections: [slack-connection, discord-connection]
    ```

    ### trigger

    The trigger represents the status condition to check before sending the notification.

    ```yaml
    >>> notification:
    >>>   trigger: succeeded
    ```

    In this example, the notification will be sent if the run succeeds.
    """

    _IDENTIFIER = "notification"

    connections: List[StrictStr]
    trigger: Optional[V1Statuses]

    def to_operator(self):
        data = super().to_dict()
        data["trigger"] = self.trigger.capitalize()
        return data
