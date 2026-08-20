from .._common import MockProfileAdapter
from ...core import AdapterMode


class AgriStackRealAdapter(MockProfileAdapter):
    mode = AdapterMode.REAL

    def fetch_profile(self, consent, farmer_ref):
        raise RuntimeError("AgriStack real adapter requires an API Setu credential")
