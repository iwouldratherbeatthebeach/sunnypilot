#!/usr/bin/env bash
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
