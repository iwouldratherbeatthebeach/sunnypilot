#!/usr/bin/env python3
"""
Patch a sunnypilot/openpilot-style repo to disable cloud upload and remote-connect
processes by default while preserving safety-critical and local logging processes.
Run from repo root. Intended for GitHub Actions or local use.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
START = "# >>> SP_PRIVACY_NO_CLOUD_PATCH"
END = "# <<< SP_PRIVACY_NO_CLOUD_PATCH"

CLOUD_PATCH = f"""
{START}
# Privacy fork: do not start cloud upload, remote-connect, livestream, or
# sunnylink network processes unless explicitly re-enabled for development with:
#   SP_ALLOW_CLOUD_UPLOADS=1
# This intentionally preserves local logging, encoderd, driver monitoring,
# controlsd, pandad, and panda safety enforcement.
SP_CLOUD_UPLOAD_PROCESS_NAMES = {{
    # comma/openpilot cloud + remote access
    "manage_athenad",
    "uploader",
    "stream_encoderd",
    "webrtcd",
    "statsd",
    "feedbackd",
    # sunnypilot/sunnylink cloud + remote configuration + uploader
    "manage_sunnylinkd",
    "sunnylink_registration_manager",
    "statsd_sp",
    "backup_manager",
    "sunnylink_uploader",
}}
if os.getenv("SP_ALLOW_CLOUD_UPLOADS", "").lower() not in ("1", "true", "yes", "on"):
    procs = [p for p in procs if getattr(p, "name", None) not in SP_CLOUD_UPLOAD_PROCESS_NAMES]
{END}
"""

ON_DEVICE_SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail
# Runtime cleanup for an already-installed comma device running this fork.
# This does not modify safety behavior; it only turns off cloud/link/upload params.
python3 - <<'PYDEVICE'
from openpilot.common.params import Params
p = Params()
for key in [
  "SunnylinkEnabled",
  "EnableSunnylinkUploader",
  "OnroadUploads",
  "IsLiveStreaming",
  "UploadRaw",
  "RecordFront",
]:
  try:
    p.put_bool(key, False)
    print(f"set {key}=False")
  except Exception as e:
    print(f"skip {key}: {e}")
PYDEVICE
'''

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def strip_old_patch(text: str) -> str:
    return re.sub(rf"\n?{re.escape(START)}.*?{re.escape(END)}\n?", "\n", text, flags=re.S)


def patch_process_config() -> None:
    path = ROOT / "system" / "manager" / "process_config.py"
    if not path.exists():
        die("system/manager/process_config.py not found. Run from the sunnypilot repo root.")
    text = path.read_text()
    if "import os" not in text:
        text = "import os\n" + text
    text = strip_old_patch(text)
    marker = "managed_processes = {p.name: p for p in procs}"
    if marker not in text:
        die(f"Could not find '{marker}' in {path}; inspect manually.")
    text = text.replace(marker, CLOUD_PATCH + "\n" + marker)
    path.write_text(text)
    print(f"patched {path}")


def patch_sunnylink_ui() -> None:
    # This file has moved across sunnypilot branches. Process filtering is the hard
    # privacy control; UI patching is best-effort only.
    candidates = [
        ROOT / "selfdrive" / "ui" / "sunnypilot" / "layouts" / "settings" / "sunnylink.py",
        ROOT / "sunnypilot" / "ui" / "settings" / "sunnylink.py",
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text()
        if "SP_PRIVACY_SUNNYLINK_UI_PATCH" in text:
            print(f"already patched {path}")
            return
        text = text.replace(
            "ui_state.params.put_bool(\"SunnylinkEnabled\", state)",
            "ui_state.params.put_bool(\"SunnylinkEnabled\", False)  # SP_PRIVACY_SUNNYLINK_UI_PATCH"
        )
        text = text.replace(
            "ui_state.params.put_bool(\"EnableSunnylinkUploader\", state)",
            "ui_state.params.put_bool(\"EnableSunnylinkUploader\", False)  # SP_PRIVACY_SUNNYLINK_UI_PATCH"
        )
        text = text.replace(
            "set_enabled(self._sunnylink_enabled)",
            "set_enabled(False)  # SP_PRIVACY_SUNNYLINK_UI_PATCH"
        )
        path.write_text(text)
        print(f"patched {path}")
        return
    print("sunnylink UI file not found on this branch; process-level privacy patch still applies")


def write_runtime_script() -> None:
    scripts = ROOT / "scripts"
    scripts.mkdir(exist_ok=True)
    runtime = scripts / "privacy_params_off.sh"
    runtime.write_text(ON_DEVICE_SCRIPT)
    runtime.chmod(0o755)
    print(f"wrote {runtime}")


def main() -> None:
    patch_process_config()
    patch_sunnylink_ui()
    write_runtime_script()

if __name__ == "__main__":
    main()
