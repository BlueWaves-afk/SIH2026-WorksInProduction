from .._common import MockSignalAdapter


class AgmarknetMockAdapter(MockSignalAdapter):
    def __init__(self):
        super().__init__("agmarknet", [{"metric": "mandi_price_deviation_pct", "value": {"deviation_pct": 0, "below_msp": False}, "unit": "percent"}])
