# Migration surface

Base: `434dc7105cf6d559018d15af5fecbcdad44f036e`.

| Files | Change |
| --- | --- |
| `simulations/helpers.py` | WXYZ protocol / XYZW runtime boundaries; array materialization |
| `simulations/configs/env_cfg.py` | PhysX settings and task imports |
| `simulations/configs/{object,scene,robot}_cfg.py` | Config rotations and task imports |
| `simulations/configs/event_cfg.py` | Array materialization and consistent selected-environment force masks |
| `simulations/configs/termination_cfg.py` | State materialization; tensor conjunction for pick; unchanged placement geometry |
| `simulations/robots/franka.py` | Pin content prefix; unchanged actuator values |
| `simulations/simulate.py` | Torch/Warp material API; state/action/config quaternion conversion; startup imports |
| `simulations/state_machines/sm_utils.py` | Quaternion math boundary |
| `simulations/evaluate.py` | Kit startup order, camera enablement, config lookup, sim.dt, unwrapped access, Tensor type check, controller quaternion boundary |

Policy messages remain WXYZ. No weights are converted. Explicit contact settings retain source values but do not prove identical dynamics.

The upstream `simulations/robots/PIPER` mesh/USD/URDF directory is omitted. Obtain it separately from the pinned upstream repository under applicable terms if needed; Piper is unvalidated here. DOM and NVIDIA assets are external too.

Runtime evidence from the larger working migration tree does not validate this isolated snapshot. Only tests performed on this snapshot can be claimed for it.
