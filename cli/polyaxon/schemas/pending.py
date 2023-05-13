from clipped.utils.enums import PEnum


class V1RunPending(str, PEnum):
    APPROVAL = "approval"
    UPLOAD = "upload"
    CACHE = "cache"
    BUILD = "build"
