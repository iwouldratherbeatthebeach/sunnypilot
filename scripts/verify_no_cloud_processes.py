#!/usr/bin/env python3
"""Static check for the local privacy process filter in system/manager/process_config.py."""
from pathlib import Path
import sys

path = Path("system/manager/process_config.py")
if not path.exists():
    print("Run from repo root; missing system/manager/process_config.py", file=sys.stderr)
    sys.exit(2)
text = path.read_text()
required = [
    "SP_PRIVACY_NO_CLOUD_PATCH",
    "SP_CLOUD_UPLOAD_PROCESS_NAMES",
    "manage_athenad",
    "uploader",
    "stream_encoderd",
    "webrtcd",
    "manage_sunnylinkd",
    "sunnylink_uploader",
]
missing = [s for s in required if s not in text]
if missing:
    print("Privacy patch missing expected markers/names:", missing, file=sys.stderr)
    sys.exit(1)
print("Privacy patch markers found. Cloud/link/upload processes are filtered unless SP_ALLOW_CLOUD_UPLOADS=1.")
