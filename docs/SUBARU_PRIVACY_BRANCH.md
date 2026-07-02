# sunnypilot Subaru privacy branch

This upload payload creates a branch that runs locally without the normal cloud/upload/remote-connect path enabled by default.

The process filter is intentionally narrow. It removes startup entries for upload, remote-connect, sunnylink, stats/feedback upload, backups, and stream/WebRTC debug processes. It does not remove local control, camera, logging, driver monitoring, or panda safety processes.

The Subaru vehicle support lives in `opendbc_repo`, which is a submodule in sunnypilot. Point the submodule at your patched `opendbc` fork branch when running the workflow.
