from .._common import MockSignalAdapter


class Sentinel2MockAdapter(MockSignalAdapter):
    def __init__(self):
        super().__init__("sentinel2", [{"metric": "satellite_crop_stress", "value": 0, "unit": "percent"}])
