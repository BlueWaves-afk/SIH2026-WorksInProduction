from .._common import ConfiguredRealAdapter


class MSPRealAdapter(ConfiguredRealAdapter):
    def __init__(self, endpoint: str | None = None):
        super().__init__("msp", endpoint)
