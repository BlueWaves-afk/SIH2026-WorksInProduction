from .._common import MockSignalAdapter


class MSPMockAdapter(MockSignalAdapter):
    def __init__(self):
        super().__init__("msp", [{"metric": "msp_price", "value": 0, "unit": "inr_per_quintal", "ttl": __import__("datetime").timedelta(days=365)}])
