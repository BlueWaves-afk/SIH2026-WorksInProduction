import json
import os
from datetime import datetime

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'imd_weather.json')

class MockWeatherAdapter:
    def __init__(self):
        with open(FIXTURE_PATH, 'r') as f:
            self.data = json.load(f)

    def get_rainfall_deviation(self, village_id: str, scenario: str = 'normal'):
        observations = self.data.get(scenario, [])
        for obs in observations:
            if obs['village_id'] == village_id:
                return obs
        return None

