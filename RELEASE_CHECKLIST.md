# Release checklist

- [x] Pin source; retain original credit and license.
- [x] Export without private history, environment paths, weights or experiment artifacts.
- [x] Keep model, training, inference and datasets source-identical.
- [x] Limit changes to documented simulator migration.
- [x] Do not bundle DOM, NVIDIA or Piper assets.
- [x] Test this exact executable source on Sim 6.1.0.0 / Lab 3.0.0rc1: startup, RGB, inference, natural termination, video decoding and second-episode reset (two single-environment smoke episodes).
- [x] Record tested source digest and runtime versions in VALIDATION.md.
- [x] Add a real rollout video and relative README cover/video links; do not interpret the demo as benchmark statistics.
- [ ] Check asset availability and review any future gripper calibration as a separate version.

Publish only as a **smoke-tested runtime compatibility preview**, not a benchmark-certified release. Do not transfer another snapshot's score to this one. Independent user asset availability and broader validation remain open.

Upload only this directory or its archive, not the surrounding workspace. Start a fresh Git repository if desired; no `.git` directory is included. Keep LICENSE and attribution. Review newly added files before future uploads.
