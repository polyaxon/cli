from polyaxon.exceptions import PolyaxonSchemaError


def get_queue_info(queue: str):
    if not queue:
        raise PolyaxonSchemaError("Received an invalid queue {}".format(queue))

    parts = queue.replace(".", "/").split("/")
    agent = None
    queue_name = queue
    if len(parts) == 2:
        agent, queue_name = parts
    elif len(parts) > 2:
        raise PolyaxonSchemaError(
            "Please provide a valid queue. "
            "The queue name should be: queue-name to use the default agent or agent-name/queue."
        )

    return agent, queue_name
