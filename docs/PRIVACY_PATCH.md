# Local privacy overlay for sunnypilot

This overlay disables cloud upload, remote-connect, sunnylink registration, sunnylink uploader, stats/feedback upload-style processes, and live-stream/debug WebRTC processes by default.

It preserves:

- driver monitoring
- local logging (`loggerd`, `encoderd`)
- local UI/sound
- `controlsd`
- `pandad`
- panda safety enforcement
- Subaru safety behavior

Temporary development override:

```bash
SP_ALLOW_CLOUD_UPLOADS=1 ./launch_openpilot.sh
```

Do not use that override if your goal is a no-cloud/no-remote fork.
