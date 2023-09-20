from traceml import tracking

from traceml.tracking import *  # noqa


def __getattr__(name):
    if name == "TRACKING_RUN":
        return tracking.TRACKING_RUN
