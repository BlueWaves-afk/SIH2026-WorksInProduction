from .._common import MockSignalAdapter


class BhuvanMockAdapter(MockSignalAdapter):
    def __init__(self):
        super().__init__("bhuvan", [{"metric": "village_coordinates", "value": {"lat": 20.0, "lon": 73.8}, "unit": "geojson"}])
