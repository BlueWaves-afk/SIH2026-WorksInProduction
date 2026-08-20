from .._common import ConfiguredRealAdapter


class BhuvanRealAdapter(ConfiguredRealAdapter):
    def __init__(self, endpoint: str | None = None, *, api_key: str | None = None):
        super().__init__("bhuvan", endpoint, api_key=api_key)
