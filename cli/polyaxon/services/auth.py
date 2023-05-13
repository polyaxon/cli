class AuthenticationError(Exception):
    pass


class AuthenticationTypes:
    TOKEN = "Token"
    INTERNAL_TOKEN = "InternalToken"
    EPHEMERAL_TOKEN = "EphemeralToken"

    VALUES = {TOKEN, INTERNAL_TOKEN, EPHEMERAL_TOKEN}
