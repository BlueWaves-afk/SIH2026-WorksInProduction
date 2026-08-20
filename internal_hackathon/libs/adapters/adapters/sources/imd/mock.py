from .._common import MockSignalAdapter


class IMDMockAdapter(MockSignalAdapter):
    def __init__(self):
        super().__init__("imd", [{"metric": "rainfall_deviation_pct", "value": 0, "unit": "percent"}])
