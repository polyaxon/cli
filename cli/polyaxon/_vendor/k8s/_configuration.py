class Configuration:
    """Stand-in for `kubernetes.client.Configuration` used by the vendored models.

    The models only read `client_side_validation`, which defaults to `True` upstream.
    """

    client_side_validation = True

    @classmethod
    def get_default_copy(cls) -> "Configuration":
        return cls()
