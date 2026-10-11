# Runtime smoke validation (2026-10-11)

Tested source archive SHA256: 09b3f60d91a255dc43e39b9b35c1eb5a8df11196ca5dae718468efb957998a18.
The 62-file source snapshot was verified before execution. This release adds documentation and demo media only; executable source remains identical to that tested snapshot.

Environment: Linux, Python 3.12, Isaac Sim 6.1.0.0 / Isaac Lab 3.0.0rc1; NVIDIA RTX 6000D. Separate simulator and inference environments/GPUs. Official DOM checkpoint model.safetensors SHA256: e3da8b1e0326d7a3ee6873f7fa17cdf7015201251901be5107377cb851ce3af8.

Protocol: Franka, one environment, scene 1-1_place_franka_avocado05d_O02_01048620_1690, original streaming LAAS and sleep, two consecutive episodes. No policy modifications or gripper recalibration.

| Episode | Upstream placement result | Simulator steps | Client actions | Video frames |
| --- | --- | --- | --- | --- |
| 1 | Success | 240 | 216 | 240 |
| 2 (after reset) | Success | 249 | 239 | 249 |

Both episodes terminated naturally. The client reported completed suite / total tests 2 and exited 0; the idle simulator service was subsequently cleaned up by the external supervisor. Both saved RGB videos fully decoded with ffmpeg without errors. The original queue emitted full-queue warnings and reset briefly emitted missing-state warnings; these are retained observations, not silently repaired behavior.

The demo is episode 1 in full, 240 frames at 24 fps (10 seconds), H.264, 1440x360. It is a rendered three-camera montage, not wall-clock performance evidence. Container metadata was stripped before remux; sampled frames and cover were visually reviewed without internal-path or sensitive overlays.

Scope: this establishes a limited startup/RGB/inference/termination/video/reset smoke check. It does not validate overall success rate, independent physical initial states, multiple environments, dataset generation, Piper, cross-version contact equivalence, or the paper's original environment. CPU tests provide additional boundary checks only.

Two preliminary launch attempts failed before rollouts (missing existing installation runtime environment settings; obsolete --headless CLI flag). The successful run used HEADLESS=1 and ENABLE_CAMERAS=1. No source changes were made between attempts. Users must complete NVIDIA license acceptance through their installation procedure.

Assets are not bundled. The tested installation resolved the Franka 5.1 content prefix while running Sim 6.1; availability on another installation is not guaranteed. Original S-Lab and separate dataset/simulator asset terms remain applicable.
