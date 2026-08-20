from __future__ import annotations

import os
import tempfile


os.environ.setdefault("ENV", "test")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(prefix='kisansetu-test-', suffix='.sqlite')}")
