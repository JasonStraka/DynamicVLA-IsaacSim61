# -*- coding: utf-8 -*-
#
# @File:   helpers.py
# @Author: Haozhe Xie
# @Date:   2025-10-03 19:04:52
# @Last Modified by: Haozhe Xie
# @Last Modified at: 2025-12-07 14:26:51
# @Email:  root@haozhexie.com

import importlib.util
import math

import numpy as np
import torch
from PIL import Image
from scipy.spatial.transform import Rotation as R


def _detect_xyzw_isaac_api():
    """Return whether this Isaac Lab runtime uses the 3.x XYZW API.

    Isaac Lab 3.x introduced Warp ``ProxyArray`` state buffers and changed all
    public quaternion APIs from WXYZ to XYZW.  DynamicVLA's files and policy
    protocol remain WXYZ, so conversions belong at the simulator boundary.
    """
    try:
        return importlib.util.find_spec("isaaclab.utils.warp.proxy_array") is not None
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False


_ISAAC_USES_XYZW = _detect_xyzw_isaac_api()


def config_quat_from_wxyz(quaternion):
    """Convert a legacy DynamicVLA WXYZ quaternion for Isaac config writes."""
    if not _ISAAC_USES_XYZW:
        return quaternion
    values = list(quaternion)
    converted = [values[1], values[2], values[3], values[0]]
    if isinstance(quaternion, tuple):
        return tuple(converted)
    if isinstance(quaternion, np.ndarray):
        return np.asarray(converted, dtype=quaternion.dtype)
    return converted


def quat_wxyz_to_isaac(quaternion):
    """Convert an internal WXYZ Torch quaternion for Isaac math helpers."""
    if not _ISAAC_USES_XYZW:
        return quaternion
    return quaternion[..., [1, 2, 3, 0]]


def quat_isaac_to_wxyz(quaternion):
    """Convert an Isaac math result back to DynamicVLA's WXYZ protocol."""
    if not _ISAAC_USES_XYZW:
        return quaternion
    return quaternion[..., [3, 0, 1, 2]]


def config_quaternions_to_wxyz(value):
    """Return a JSON-ready config that obeys the external WXYZ contract.

    Isaac Lab 3 config objects hold XYZW at runtime.  DOM scene JSON remains
    WXYZ so it can be consumed by old and new runtimes without a silent second
    conversion on reload.
    """
    if not _ISAAC_USES_XYZW:
        return value
    if isinstance(value, dict):
        converted = {}
        for key, item in value.items():
            if key == "rot":
                if isinstance(item, torch.Tensor):
                    item = item.detach().cpu().tolist()
                elif isinstance(item, np.ndarray):
                    item = item.tolist()
                if isinstance(item, (list, tuple)) and len(item) == 4:
                    converted[key] = [item[3], item[0], item[1], item[2]]
                else:
                    converted[key] = config_quaternions_to_wxyz(item)
            else:
                converted[key] = config_quaternions_to_wxyz(item)
        return converted
    if isinstance(value, list):
        return [config_quaternions_to_wxyz(item) for item in value]
    if isinstance(value, tuple):
        return [config_quaternions_to_wxyz(item) for item in value]
    if isinstance(value, torch.Tensor):
        return config_quaternions_to_wxyz(value.detach().cpu().tolist())
    if isinstance(value, np.ndarray):
        return config_quaternions_to_wxyz(value.tolist())
    return value


def pose_action_wxyz_to_isaac(action):
    """Convert the quaternion slice of ``xyz + quat + gripper`` actions.

    The model/server message protocol deliberately remains WXYZ for checkpoint
    compatibility.  Only the tensor handed to Isaac's absolute-pose
    controller changes to XYZW on Lab 3.x.
    """
    if not _ISAAC_USES_XYZW:
        return action
    converted = action.clone()
    converted[..., 3:7] = quat_wxyz_to_isaac(action[..., 3:7])
    return converted


def pose_action_isaac_to_wxyz(action):
    """Convert a Lab 3 controller action back to the policy protocol."""
    if not _ISAAC_USES_XYZW:
        return action
    converted = action.clone()
    converted[..., 3:7] = quat_isaac_to_wxyz(action[..., 3:7])
    return converted


def as_torch(value, quaternion=False):
    """Return an Isaac Lab state value as a Torch tensor.

    Isaac Lab 3 exposes simulation state through Warp ``ProxyArray`` objects.
    Their quaternion Torch view is XYZW, while DynamicVLA's saved data and
    policy protocol remain WXYZ.  Ordinary tensors (the Isaac Lab 2 interface)
    are already WXYZ and must not be reordered.  Callers that invoke Isaac
    math helpers must convert back with :func:`quat_wxyz_to_isaac` first.
    """
    if isinstance(value, torch.Tensor):
        return value

    tensor = getattr(value, "torch", None)
    if tensor is None:
        return value
    if callable(tensor):
        tensor = tensor()
    if quaternion:
        tensor = tensor[..., [3, 0, 1, 2]]
    return tensor


def as_numpy(value):
    """Materialize simulator array wrappers as ordinary NumPy arrays."""
    if isinstance(value, np.ndarray):
        return value
    value = as_torch(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().numpy()
    numpy_value = getattr(value, "numpy", None)
    if numpy_value is not None:
        return numpy_value() if callable(numpy_value) else numpy_value
    return np.asarray(value)


def get_semantic_tags():
    KNOWN_TAGS = {"ROBOT": 1, "OBJECT_MAIN": 2, "CONTAINER_MAIN": 3}
    for i in range(8):  # Support up to 8 background objects/containers
        KNOWN_TAGS["OBJECT%02d" % (i + 1)] = 4 + i
        KNOWN_TAGS["CONTAINER%02d" % (i + 1)] = 12 + i

    return KNOWN_TAGS


def get_semantic_map(mask):
    PALETTE = np.array([[i, i, i] for i in range(256)])
    PALETTE[:16] = np.array(
        [
            [0, 0, 0],
            [128, 0, 0],
            [0, 128, 0],
            [128, 128, 0],
            [0, 0, 128],
            [128, 0, 128],
            [0, 128, 128],
            [128, 128, 128],
            [64, 0, 0],
            [191, 0, 0],
            [64, 128, 0],
            [191, 128, 0],
            [64, 0, 128],
            [191, 0, 128],
            [64, 128, 128],
            [191, 128, 128],
        ]
    )
    mask = Image.fromarray(mask.astype(np.uint8), mode="P")
    mask.putpalette(PALETTE.reshape(-1).tolist())
    return np.array(mask.convert("RGB"))


def get_object_relative_bbox(object_size, object_quat_w, robot_quat):
    from isaaclab.utils.math import quat_apply

    batch_size = object_quat_w.size(0)
    object_size_rot = torch.eye(3, device=object_size.device) * object_size
    # object_size_rot = torch.eye(3, device=object_size.device).unsqueeze(0) * object_size.unsqueeze(-1)
    object_quat_isaac = quat_wxyz_to_isaac(object_quat_w)
    object_size_x_rot = quat_apply(
        object_quat_isaac,
        object_size_rot[0:1, :].repeat(batch_size, 1),
    )
    object_size_y_rot = quat_apply(
        object_quat_isaac,
        object_size_rot[1:2, :].repeat(batch_size, 1),
    )
    object_size_z_rot = quat_apply(
        object_quat_isaac,
        object_size_rot[2:3, :].repeat(batch_size, 1),
    )
    return torch.cat(
        [
            get_robot_relative_position(object_size_x_rot, robot_quat).unsqueeze(1),
            get_robot_relative_position(object_size_y_rot, robot_quat).unsqueeze(1),
            get_robot_relative_position(object_size_z_rot, robot_quat).unsqueeze(1),
        ],
        dim=1,
    )


def get_robot_relative_position(point, robot_quat):
    from isaaclab.utils.math import quat_apply, quat_inv

    # inv_quat = scipy.spatial.transform.Rotation.from_quat(robot_quat).inv()
    # inv_offset = inv_quat.apply(point)
    robot_quat_isaac = quat_wxyz_to_isaac(robot_quat)
    return quat_apply(quat_inv(robot_quat_isaac), point)


def is_object_placed(
    object_position: torch.Tensor,
    object_projected_size: torch.Tensor,
    container_position: torch.Tensor,
    container_projected_size: torch.Tensor,
    tolerance: float = 0.015,
) -> torch.Tensor:
    # Horizonal
    container_relative_size = container_projected_size / 2 + tolerance
    container_axis_lengths = torch.norm(container_relative_size, dim=2)
    container_axis_dirs = container_relative_size / container_axis_lengths.unsqueeze(2)

    object_container_rela = object_position - container_position
    object_container_projections = torch.matmul(
        container_axis_dirs, object_container_rela.unsqueeze(-1)
    ).squeeze(-1)

    object_container_projections_xy = object_container_projections[:, :2]
    container_axis_lengths_xy = container_axis_lengths[:, :2]
    is_horizonal_in_container = torch.all(
        torch.abs(object_container_projections_xy) <= container_axis_lengths_xy, dim=1
    )

    # Vertical
    object_relative_size = object_projected_size / 2
    object_lowest_z = object_position[:, 2] - torch.sum(
        torch.abs(object_relative_size[:, :, 2]), dim=1
    )
    container_highest_z = container_position[:, 2] + torch.sum(
        torch.abs(container_relative_size[:, :, 2]), dim=1
    )
    is_vertical_in_container = object_lowest_z <= container_highest_z

    return torch.logical_and(is_horizonal_in_container, is_vertical_in_container)



def get_object_tags(object_type, object_states, robot_pose, skip_tags, tag_thresholds):
    robot_quat_xyzw = np.roll(robot_pose["quat"].astype(np.float32), -1)
    _get_relative_pos = lambda point: R.from_quat(robot_quat_xyzw).apply(
        point - robot_pose["pos"], inverse=True
    )
    TAG_FUNCTIONS = {
        "HEIGHT": lambda x: x["pos"][2],
        "AREA": lambda x: x["size"][0] * x["size"][1],
        "VOLUME": lambda x: np.prod(x["size"]),
        "POSITION_FROM_LEFT": lambda x: _get_relative_pos(x["pos"])[1],
        "POSITION_FROM_BOTTOM": lambda x: -_get_relative_pos(x["pos"])[0],
        "DISTANCE_FROM_ROBOT": lambda x: -np.linalg.norm(x["pos"] - robot_pose["pos"]),
    }
    assert object_type in [
        "objects",
        "containers",
    ], f"Unknown object type: {object_type}"

    if len(object_states) > 1:
        for tag, func in TAG_FUNCTIONS.items():
            if skip_tags is None or tag not in skip_tags:
                object_states = _get_state_tag(
                    object_type, object_states, tag, func, tag_thresholds
                )
        # Generate additional direction tags
        if skip_tags is None or "VELOCITY" not in skip_tags:
            object_states = _get_direction_tags(
                object_type, object_states, robot_quat_xyzw
            )
            object_states = _get_velocity_tags(
                object_type, object_states, tag_thresholds
            )
    # Remove duplicate tags (causing confusion in instruction generation)
    return _get_unique_tags([os["tags"] for os in object_states])


def _get_state_tag(object_type, object_states, tag_name, tag_func, tag_thresholds):
    RANK_TAGS = {
        "FIRST": {
            "HEIGHT": "the tallest %s",
            "AREA": "the %s with the largest area",
            "VOLUME": "the %s with the largest volume",
            "POSITION_FROM_LEFT": "the %s that is closest to the robot's left at the start",
            "POSITION_FROM_BOTTOM": "the %s closest to the robot mounting edge at the start",
            "DISTANCE_FROM_ROBOT": "the %s closest to the robot at the start",
        },
        "LAST": {
            "HEIGHT": "the shortest %s",
            "AREA": "the %s with the smallest area",
            "VOLUME": "the %s with the smallest volume",
            "POSITION_FROM_LEFT": "the %s that is closest to the robot's right at the start",
            "POSITION_FROM_BOTTOM": "the %s farthest from the robot mounting edge at the start",
            "DISTANCE_FROM_ROBOT": "the %s farthest from the robot at the start",
        },
        "MEDIUM": {
            "HEIGHT": "the %s of medium height",
            "AREA": "the %s with medium area",
            "VOLUME": "the %s with medium volume",
            "POSITION_FROM_LEFT": "the %s in the middle from left to right at the start",
            "POSITION_FROM_BOTTOM": "the %s with medium distance to the robot mounting edge at the start",
            "DISTANCE_FROM_ROBOT": "the %s with medium distance to the robot at the start",
        },
    }

    n = len(object_states)
    sorted_states = sorted(object_states, key=tag_func, reverse=True)
    last_value = tag_func(sorted_states[-1])
    cur_rank = 1
    for i, state in enumerate(sorted_states):
        object_name = (
            object_type.rstrip("s") if object_type == "objects" else state["category"]
        )
        cur_value = tag_func(state)
        if abs(cur_value - last_value) > tag_thresholds.get(tag_name.lower()):
            cur_rank = i + 1
        if cur_rank == 1:
            state["tags"].append(RANK_TAGS["FIRST"][tag_name] % object_name)
        elif cur_rank == n:
            state["tags"].append(RANK_TAGS["LAST"][tag_name] % object_name)
        elif cur_rank == 2 and n == 3:
            state["tags"].append(RANK_TAGS["MEDIUM"][tag_name] % object_name)

        if n == 2:  # e.g., "tallest" -> "taller"
            state["tags"][-1] = state["tags"][-1].replace("est", "er")

        last_value = cur_value

    return object_states


def _get_velocity_tags(object_type, object_states, tag_thresholds):
    RANK_TAGS = {
        "FIRST": "the moving %s with the highest initial velocity",
        "LAST": "the moving %s with the lowest initial velocity",
        "MEDIUM": "the moving %s with medium initial velocity",
    }
    tag_func = lambda x: (np.linalg.norm(x["lin_vel"]) if "lin_vel" in x else 0)

    sorted_states = sorted(
        [obj for obj in object_states if tag_func(obj) >= 0.01],
        key=tag_func,
        reverse=True,
    )
    n = len(sorted_states)
    if n > 0:
        last_value = 0.01 - tag_thresholds.get("velocity")
        cur_rank = 1
        for i, state in enumerate(sorted_states):
            object_name = (
                object_type.rstrip("s")
                if object_type == "objects"
                else state["category"]
            )
            cur_value = tag_func(state)
            if abs(cur_value - last_value) > tag_thresholds.get("velocity"):
                cur_rank = i + 1
            if cur_rank == 1:
                state["tags"].append(RANK_TAGS["FIRST"] % object_name)
            elif cur_rank == n:
                state["tags"].append(RANK_TAGS["LAST"] % object_name)
            elif cur_rank == 2 and n == 3:
                state["tags"].append(RANK_TAGS["MEDIUM"] % object_name)

            if n == 2:  # e.g., "tallest" -> "taller"
                state["tags"][-1] = state["tags"][-1].replace("est", "er")

            last_value = cur_value

    return object_states


def _get_direction_tags(object_type, object_states, robot_quat):
    DIRECTION_TAGS = [
        "the %s moving in the robot's forward direction",
        "the %s moving in the robot's forward-left direction",
        "the %s moving in the robot's left direction",
        "the %s moving in the robot's backward-left direction",
        "the %s moving in the robot's backward direction",
        "the %s moving in the robot's backward-right direction",
        "the %s moving in the robot's right direction",
        "the %s moving in the robot's forward-right direction",
    ]
    for state in object_states:
        object_name = (
            object_type.rstrip("s") if object_type == "objects" else state["category"]
        )
        if "lin_vel" not in state or np.linalg.norm(state["lin_vel"]) < 0.01:
            state["tags"].append("stationary %s" % object_name)
            continue

        idx = get_direction_index(state["lin_vel"], robot_quat)
        state["tags"].append(DIRECTION_TAGS[idx] % object_name)

    return object_states


def get_direction_index(linear_velocity, robot_quat=None, inverse=True):
    if robot_quat is not None:
        linear_velocity = R.from_quat(robot_quat).apply(
            linear_velocity, inverse=inverse
        )

    angle = math.degrees(math.atan2(linear_velocity[1], linear_velocity[0])) % 360
    # idx = int((angle + 22.5) // 45) % 8  # Old version
    # front: [345°, 360) U [0°, 15°); back:  [165°, 195°); left:  [75°, 105°);
    # right: [255, 285°)
    if angle >= 345 or angle < 15:
        idx = 0  # front (20°)
    elif angle >= 15 and angle < 75:
        idx = 1  # front-left
    elif angle >= 75 and angle < 105:
        idx = 2  # left (20°)
    elif angle >= 105 and angle < 165:
        idx = 3  # back-left
    elif angle >= 165 and angle < 195:
        idx = 4  # back (20°)
    elif angle >= 195 and angle < 255:
        idx = 5  # back-right
    elif angle >= 255 and angle < 285:
        idx = 6  # right (20°)
    elif angle >= 285 and angle < 345:
        idx = 7  # front-right

    return idx


def _get_unique_tags(object_tags):
    assert isinstance(object_tags, list)
    if len(object_tags) == 0:
        return []

    target_tags = set(object_tags[0])
    other_tags = set(tag for obj in object_tags[1:] for tag in obj)
    return list(target_tags - other_tags)
