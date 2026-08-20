from __future__ import annotations

import sys
from pathlib import Path


def template_brief_builder():
    try:
        from ai_copilot.agents.officer_copilot_graph import build_template_brief

        return build_template_brief
    except ModuleNotFoundError:
        root = Path(__file__).resolve().parents[4]
        package = root / "services" / "ai-copilot"
        if str(package) not in sys.path:
            sys.path.insert(0, str(package))
        from ai_copilot.agents.officer_copilot_graph import build_template_brief

        return build_template_brief
