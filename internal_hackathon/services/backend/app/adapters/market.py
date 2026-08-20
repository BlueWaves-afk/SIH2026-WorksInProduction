import json
import os

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'agmarknet_prices.json')

class MockMarketAdapter:
    def __init__(self):
        with open(FIXTURE_PATH, 'r') as f:
            self.data = json.load(f)

    def get_price_deviation(self, commodity: str, scenario: str = 'normal'):
        quotes = self.data.get(scenario, [])
        for quote in quotes:
            if quote['commodity'].lower() == commodity.lower():
                return quote
        return None

