from .._common import ConfiguredRealAdapter


class Sentinel2RealAdapter(ConfiguredRealAdapter):
    def __init__(self, endpoint: str | None = None):
        super().__init__("sentinel2", endpoint)
