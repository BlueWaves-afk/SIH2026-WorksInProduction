from .._common import ConfiguredRealAdapter


class SoilRealAdapter(ConfiguredRealAdapter):
    def __init__(self, endpoint: str | None = None, *, api_key: str | None = None):
        super().__init__("soil", endpoint, api_key=api_key)
