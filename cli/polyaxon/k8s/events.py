def get_container_statuses_by_name(statuses):
    return {
        container_status["name"]: {
            "ready": container_status["ready"],
            "state": container_status["state"],
        }
        for container_status in statuses
    }


def get_container_status(statuses, container_ids):
    job_container_status = None
    for container_id in container_ids:
        job_container_status = statuses.get(container_id)
        if job_container_status:
            break
    return job_container_status
