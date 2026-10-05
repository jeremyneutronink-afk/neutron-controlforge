import os
import sys
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]

SDK_PATH = (
    ROOT
    / "sdk"
    / "python"
)

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

if str(SDK_PATH) not in sys.path:
    sys.path.insert(
        0,
        str(SDK_PATH),
    )


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)

os.environ.setdefault(
    "AGENTGUARD_ADMIN_KEY",
    "test-admin-key-not-for-production",
)

os.environ.setdefault(
    "SYSTEM_TEST_BASE_URL",
    "http://127.0.0.1:8000",
)
