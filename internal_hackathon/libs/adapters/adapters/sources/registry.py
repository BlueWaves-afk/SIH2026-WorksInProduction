from __future__ import annotations

import os

from ..core import AdapterMode, AdapterRegistry
from .agmarknet import AgmarknetMockAdapter, AgmarknetRealAdapter
from .agristack import AgriStackMockAdapter, AgriStackRealAdapter
from .bhashini import BhashiniMockAdapter, BhashiniRealAdapter
from .bhuvan import BhuvanMockAdapter, BhuvanRealAdapter
from .imd import IMDMockAdapter, IMDRealAdapter
from .msp import MSPMockAdapter, MSPRealAdapter
from .sentinel2 import Sentinel2MockAdapter, Sentinel2RealAdapter
from .soil import SoilMockAdapter, SoilRealAdapter


def build_registry(environ: dict[str, str] | None = None) -> AdapterRegistry:
    env = environ or os.environ
    registry = AdapterRegistry()
    factories = {
        "imd": (IMDMockAdapter, IMDRealAdapter),
        "agmarknet": (AgmarknetMockAdapter, AgmarknetRealAdapter),
        "agristack": (AgriStackMockAdapter, AgriStackRealAdapter),
        "bhashini": (BhashiniMockAdapter, BhashiniRealAdapter),
        "bhuvan": (BhuvanMockAdapter, BhuvanRealAdapter),
        "msp": (MSPMockAdapter, MSPRealAdapter),
        "sentinel2": (Sentinel2MockAdapter, Sentinel2RealAdapter),
        "soil": (SoilMockAdapter, SoilRealAdapter),
    }
    for source, (mock_factory, real_factory) in factories.items():
        raw = env.get(f"ADAPTER_MODE_{source.upper()}", "mock").lower()
        mode = AdapterMode(raw)
        if mode is AdapterMode.REAL:
            endpoint = env.get(f"{source.upper()}_ENDPOINT")
            api_key = env.get(f"{source.upper()}_API_KEY")
            if source in {"imd", "agmarknet"}:
                try:
                    timeout = float(env.get("LIVE_ADAPTER_TIMEOUT_SECONDS", "10"))
                except ValueError:
                    timeout = 10.0
                adapter = real_factory(endpoint=endpoint, api_key=api_key, timeout_seconds=timeout)
            elif source in {"bhuvan", "msp", "sentinel2", "soil"}:
                api_key = env.get(f"{source.upper()}_API_KEY")
                adapter = real_factory(endpoint=endpoint, api_key=api_key)
            else:
                adapter = real_factory()
        else:
            adapter = mock_factory()
        registry.register(source, adapter)
    return registry
