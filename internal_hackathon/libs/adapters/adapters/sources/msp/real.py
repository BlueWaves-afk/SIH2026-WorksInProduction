from .._common import ConfiguredRealAdapter


class MSPRealAdapter(ConfiguredRealAdapter):
    def __init__(self, endpoint: str | None = None, *, api_key: str | None = None):
        super().__init__("msp", endpoint, api_key=api_key)
