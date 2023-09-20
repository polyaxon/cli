from polyaxon._sdk.async_client.api_client import AsyncApiClient
from polyaxon._sdk.sync_client.api_client import ApiClient


class BaseApi:
    def __init__(self, api_client=None, is_async=False):
        if api_client is None:
            api_client = (
                AsyncApiClient.get_default() if is_async else ApiClient.get_default()
            )
        self.api_client = api_client
