# Dynamic Bench — Isaac Sim 6.1 compatibility preview

Unofficial compatibility port of [DynamicVLA](https://github.com/hzxie/DynamicVLA), based on commit `434dc7105cf6d559018d15af5fecbcdad44f036e`. Original authors, citation and license are retained.

**Smoke-tested compatibility preview, not an official release or paper-success-rate reproduction.** This isolated source snapshot completed two consecutive single-environment GPU episodes on 2026-10-11. See [VALIDATION.md](VALIDATION.md) for evidence and limits; results from other snapshots are not attributed here.

## Scope

Simulator interfaces only: quaternion boundaries, Warp state materialization, camera serialization, PhysX configuration, task imports, controller inputs and startup order. Model, training, dataset and inference implementations are unchanged from the pinned upstream snapshot. Original streaming action queue, inference wait and reset/ACK behavior remain upstream code.

The preview targets **Franka, one environment**. The inherited multi-environment option is not validated per-environment benchmark accounting: upstream termination and video handling are not independent per-slot accounting. Dataset generation and Piper are also unvalidated in this clean package.

## Environment and usage

Target: Linux, Python 3.12, Isaac Sim **6.1.0.0**, Isaac Lab **3.0.0rc1**, PhysX backend. This early-release API target does not promise compatibility with every later 3.x version. Refer to the [Isaac Lab migration guide](https://isaac-sim.github.io/IsaacLab/v3.0.0-EA/source/migration/migrating_to_isaaclab_3-0.html). Keep simulation and inference in separate environments.

Install the pinned Isaac stack following NVIDIA's instructions. Add `shapely pyzmq h5py` in the simulator environment. Follow [upstream model instructions](README.upstream.md) for inference; do not install model requirements indiscriminately into the simulator environment.

Obtain DOM testing scenes, objects and the official checkpoint using upstream links; none are bundled. Test-list entries must resolve from the working directory; prefer absolute paths. In the simulator environment, from this folder:

```bash
HEADLESS=1 ENABLE_CAMERAS=1 python simulations/evaluate.py --num_envs 1 \
  --scene_dir /path/to/scenes --object_dir /path/to/objects \
  --env_cfg /path/to/test-envs.txt --output_dir /path/to/results \
  -n 20 --save
```

Cameras are enabled directly in AppLauncher; the old camera CLI flag is unnecessary. This target no longer accepts the old --headless flag; use HEADLESS=1. Complete NVIDIA's license acceptance through your installation procedure before unattended execution. In a separate model environment/terminal:

```bash
python scripts/inference.py -p /path/to/official-checkpoint -r euler -d -s
```

Use separate visible GPUs for simulation and inference when available. Keep sockets on trusted loopback: the inherited Python-object deserialization protocol is unsafe on untrusted networks.

## Version boundaries

- Authors identify Sim 4.5 / Lab 2.2.1 as the paper reference environment. This port is not that environment.
- Gripper parameters remain those of the pinned upstream snapshot: Franka finger velocity limit 0.05 m/s, friction 0.2. No cross-version contact equivalence is claimed; later upstream gripper corrections are not incorporated.
- Franka uses the 5.1 content URL prefix with the 6.1 runtime. No NVIDIA asset is bundled; validate availability in your installation.
- Original placement-success geometry is retained. Pick uses elementwise tensor conjunction; no new success metric is introduced.
- GPU startup, RGB video, real inference, natural termination, full video decoding and second-episode reset were smoke-tested on this snapshot. Other scenes, robots, batched accounting and benchmark success-rate reproduction remain unvalidated.

## CPU tests

With NumPy and PyTorch installed:

```bash
python -B -m unittest discover -s tests -v
```

See [MIGRATION.md](MIGRATION.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). No Git history, checkpoints, experiment outputs or robot meshes are included.

## License

The original [S-Lab License 1.0](LICENSE), including its non-commercial restriction, is retained. This is not MIT/Apache relicensing. Refer commercial permissions to the original contributors. Simulator software, assets and datasets have separate terms and are obtained externally. No author or NVIDIA endorsement is implied.
