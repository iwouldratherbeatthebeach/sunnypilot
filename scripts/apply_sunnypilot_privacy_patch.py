#!/usr/bin/env python3
"""
Patch a sunnypilot fork to disable cloud upload / remote-connect processes while
leaving local logging, driver monitoring, controlsd, and panda safety intact.
Run from the root of your sunnypilot fork.
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
# Aaron/privacy fork: do not start cloud upload, remote-connect, livestream, or
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

README_TEXT = """# sunnypilot privacy patch

This fork patch disables cloud upload / remote-connect processes by default while preserving local safety-critical behavior.

Disabled by default:

- comma/openpilot `uploader`
- comma/openpilot `manage_athenad`
- road livestream process `stream_encoderd`
- WebRTC debug/remote process `webrtcd`
- `statsd` / `feedbackd` upload-style processes
- sunnypilot `manage_sunnylinkd`
- sunnypilot `sunnylink_registration_manager`
- sunnypilot `statsd_sp`
- sunnypilot `backup_manager`
- sunnypilot `sunnylink_uploader`

Preserved:

- local `loggerd` and `encoderd` so you still have local logs for debugging
- driver monitoring
- `controlsd`, `pandad`, panda safety, Subaru safety tests
- local UI and core onroad/offroad operation

Temporary development override:

```bash
SP_ALLOW_CLOUD_UPLOADS=1 ./launch_openpilot.sh
```

Do not use that override if your goal is a no-cloud fork.
"""

ON_DEVICE_SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail
# Runtime cleanup for an already-installed comma device running this fork.
# This does not modify safety behavior; it only turns off cloud/link/upload params.
python3 - <<'PY'
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
PY
'''

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def require_repo() -> None:
    if not (ROOT / "system" / "manager" / "process_config.py").exists():
        die("Run this from the root of a sunnypilot/openpilot-style repo; system/manager/process_config.py not found.")


def strip_old_patch(text: str) -> str:
    return re.sub(rf"\n?{re.escape(START)}.*?{re.escape(END)}\n?", "\n", text, flags=re.S)


def patch_process_config() -> None:
    path = ROOT / "system" / "manager" / "process_config.py"
    text = path.read_text()
    if "import os" not in text:
        text = "import os\n" + text
    text = strip_old_patch(text)
    marker = "managed_processes = {p.name: p for p in procs}"
    if marker not in text:
        die(f"Could not find '{marker}' in {path}; inspect process_config.py manually.")
    text = text.replace(marker, CLOUD_PATCH + "\n" + marker)
    path.write_text(text)
    print(f"patched {path}")


def patch_sunnylink_ui() -> None:
    path = ROOT / "selfdrive" / "ui" / "sunnypilot" / "layouts" / "settings" / "sunnylink.py"
    if not path.exists():
        print(f"skip {path}: not present in this branch")
        return
    text = path.read_text()
    if "SP_PRIVACY_SUNNYLINK_UI_PATCH" in text:
        print(f"already patched {path}")
        return
    pattern = r"(?P<indent>\s*)def _sunnylink_toggle_callback\(self, state: bool\):\n(?P<body>(?:\1  .*\n)+)(?=\1def _update_description)"
    m = re.search(pattern, text)
    if not m:
        print(f"warn: could not auto-patch Sunnylink toggle callback in {path}; process-level cloud disable still applies")
        return
    indent = m.group("indent")
    repl = f"""{indent}def _sunnylink_toggle_callback(self, state: bool):\n{indent}  # SP_PRIVACY_SUNNYLINK_UI_PATCH: sunnylink/cloud linking is disabled in this privacy fork.\n{indent}  ui_state.params.put_bool(\"SunnylinkEnabled\", False)\n{indent}  ui_state.params.put_bool(\"EnableSunnylinkUploader\", False)\n{indent}  self._update_description(False)\n{indent}  return\n"""
    text = text[:m.start()] + repl + text[m.end():]
    text = text.replace(
        "self._sunnylink_uploader_toggle.action_item.set_enabled(self._sunnylink_enabled)",
        "self._sunnylink_uploader_toggle.action_item.set_enabled(False)  # SP_PRIVACY_SUNNYLINK_UI_PATCH"
    )
    path.write_text(text)
    print(f"patched {path}")


def write_docs_and_scripts() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "PRIVACY_PATCH.md").write_text(README_TEXT)
    scripts = ROOT / "scripts"
    scripts.mkdir(exist_ok=True)
    runtime = scripts / "privacy_params_off.sh"
    runtime.write_text(ON_DEVICE_SCRIPT)
    runtime.chmod(0o755)
    print(f"wrote {docs / 'PRIVACY_PATCH.md'}")
    print(f"wrote {runtime}")


def main() -> None:
    require_repo()
    patch_process_config()
    patch_sunnylink_ui()
    write_docs_and_scripts()
    print("\nPrivacy patch applied. Review the diff, then commit it:")
    print("  git diff")
    print("  git add system/manager/process_config.py selfdrive/ui/sunnypilot/layouts/settings/sunnylink.py docs/PRIVACY_PATCH.md scripts/privacy_params_off.sh")
    print("  git commit -m 'privacy: disable cloud uploads and sunnylink by default'")
    print("\nVerification:")
    print("  python3 scripts/verify_no_cloud_processes.py")


if __name__ == "__main__":
    main()
