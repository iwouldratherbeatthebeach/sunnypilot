# Safety and privacy notes

## Preserved safety-critical pieces

This kit is designed to avoid changing safety enforcement:

- Driver monitoring stays enabled.
- `controlsd`, `pandad`, and panda safety stay enabled.
- Local logging stays enabled for debugging.
- Subaru LKAS work is applied through opendbc PRs that include safety-model/test changes instead of bypasses.

## Disabled cloud / remote pieces

The privacy patch filters cloud and remote processes after the process list is built:

- comma/openpilot uploader and remote access: `uploader`, `manage_athenad`, `stream_encoderd`, `webrtcd`
- telemetry-style helpers: `statsd`, `feedbackd`
- sunnylink: `manage_sunnylinkd`, `sunnylink_registration_manager`, `statsd_sp`, `backup_manager`, `sunnylink_uploader`

The filter is intentionally centralized in `system/manager/process_config.py` so it is easy to audit.

## What this does not do

- It does not disable driver monitoring.
- It does not change driver-distraction timeouts.
- It does not disable local route logging.
- It does not alter panda safety limits or safety hooks.
- It does not guarantee that future upstream changes cannot add a new network process; rerun the verification script and audit diffs after updates.

## Audit commands

```bash
grep -R "PythonProcess(\|DaemonProcess(\|NativeProcess(" -n system selfdrive sunnypilot | grep -Ei 'upload|athena|sunnylink|webrtc|stream|stats|feedback'
python3 scripts/verify_no_cloud_processes.py
```

## Recommended validation before driving

```bash
scons -u -j$(nproc)
pytest -q opendbc_repo/opendbc/safety/tests || true
pytest -q selfdrive/car/tests || true
```

Exact test paths can vary across sunnypilot branches.
