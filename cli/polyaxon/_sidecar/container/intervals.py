def get_sync_interval(interval: int, sleep_interval: int) -> int:
    # Infinite counter (wait until the end)
    if interval <= 0:
        return -1

    # Infinite counter
    if interval < sleep_interval:
        return 0

    # Use division to get counter
    return (interval // sleep_interval) + 1
