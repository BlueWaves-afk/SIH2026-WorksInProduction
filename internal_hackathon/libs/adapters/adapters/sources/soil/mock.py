from .._common import MockSignalAdapter


class SoilMockAdapter(MockSignalAdapter):
    def __init__(self):
        super().__init__("soil", [{"metric": "soil_water_holding_capacity", "value": "medium", "unit": "class"}])
