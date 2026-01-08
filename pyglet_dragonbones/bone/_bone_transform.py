from typing import TYPE_CHECKING, TypedDict, Literal
import math
from ..config import config

if TYPE_CHECKING:
    from .bone import Bone

fps = config.fps


class BetweenAnimationsType(TypedDict):
    angle: float
    position: float
    scale: float


class SmoothingEnabledType(TypedDict):
    angle: bool
    position: bool
    scale: bool


class SmoothingSpeedType(TypedDict):
    between_animations: BetweenAnimationsType
    angle: float
    position: float
    scale: float


def rotate_position(position, angle):
    x, y = position
    rad_angle = math.radians(-angle)
    return (
        x * math.cos(rad_angle) - y * math.sin(rad_angle),
        x * math.sin(rad_angle) + y * math.cos(rad_angle),
    )


class BoneTransform:
    base_position: tuple[float, float]
    base_angle = 0.0
    base_scale: tuple[float, float]

    _target_relative_position: tuple[float, float] | None = None
    _target_relative_angle: float | None = None
    _target_relative_scale: tuple[float, float] | None = None

    _target_angle: float | None = None
    _target_scale: tuple[float, float] | None = None

    def __init__(
        self,
        bone_info,
        bone: "Bone",
    ):
        self.bone = bone

        self.base_position = (
            (
                bone_info["transform"]["x"]
                if "transform" in bone_info and "x" in bone_info["transform"]
                else 0.0
            ),
            (
                bone_info["transform"]["y"]
                if "transform" in bone_info and "y" in bone_info["transform"]
                else 0.0
            ),
        )
        self.base_scale = (
            (
                bone_info["transform"]["scX"]
                if "transform" in bone_info and "scX" in bone_info["transform"]
                else 1.0
            ),
            (
                bone_info["transform"]["scY"]
                if "transform" in bone_info and "scY" in bone_info["transform"]
                else 1.0
            ),
        )

        if "transform" in bone_info and "skX" in bone_info["transform"]:
            a = bone_info["transform"]["skX"]
            if a < 0:
                a = 360 + a
            self.base_angle = a

        self.smoothing_speed_timer = {
            "between_animations": 5,
            "current": 0,
        }
        self.smoothing_speed: SmoothingSpeedType = {
            "between_animations": {
                "angle": 0.15,
                "position": 0.15,
                "scale": 0.15,
            },
            "angle": 1,
            "position": 1,
            "scale": 1,
        }
        self.smoothing_enabled: SmoothingEnabledType = {
            "angle": True,
            "position": True,
            "scale": True,
        }

    def set_smoothing(
        self,
        angle: bool | None = None,
        position: bool | None = None,
        scale: bool | None = None,
    ):
        """
        Enable or disable smoothing for angle, position, and scale.
        If a parameter is None, its current setting is unchanged.
        """
        if angle is not None:
            self.smoothing_enabled["angle"] = angle
        if position is not None:
            self.smoothing_enabled["position"] = position
        if scale is not None:
            self.smoothing_enabled["scale"] = scale

    def on_animation_start(self):
        self.smoothing_speed_timer["current"] = self.smoothing_speed_timer[
            "between_animations"
        ]
        self.smoothing_speed["angle"] = self.smoothing_speed["between_animations"][
            "angle"
        ]
        self.smoothing_speed["position"] = self.smoothing_speed["between_animations"][
            "position"
        ]
        self.smoothing_speed["scale"] = self.smoothing_speed["between_animations"][
            "scale"
        ]

    def _update_position(self):
        anchored_position = (
            self.bone.relative_position[0] + self.base_position[0],
            self.bone.relative_position[1] + self.base_position[1],
        )
        scaled_position = (
            anchored_position[0] * self.bone.parent.scale[0],
            anchored_position[1] * self.bone.parent.scale[1],
        )
        rotated_position = rotate_position(scaled_position, self.bone.parent.angle)
        self.bone.position = (
            self.bone.parent.position[0] + rotated_position[0],
            self.bone.parent.position[1] + rotated_position[1],
        )

    def _update_angle(self):
        scaled_angle = (
            self.bone.relative_angle * self.bone.scale[0] * self.bone.scale[1]
        )
        anchored_angle = scaled_angle + self.base_angle

        parent_angle = self.bone.parent.angle
        if hasattr(self.bone.parent, "skeleton_path"):
            parent_angle += 180

        self.target_angle = parent_angle + anchored_angle

    def _update_scale(self):
        anchored_scale = (
            self.bone.relative_scale[0] * self.base_scale[0],
            self.bone.relative_scale[1] * self.base_scale[1],
        )

        parent_scale = self.bone.parent.scale
        if hasattr(self.bone.parent, "skeleton_path"):
            parent_scale = (parent_scale[0] * -1, parent_scale[1])

        self.target_scale = (
            parent_scale[0] * anchored_scale[0],
            parent_scale[1] * anchored_scale[1],
        )

    def _update_relative_position_to_target(self, dt):
        if self.target_relative_position is None:
            return

        if not self.smoothing_enabled["position"]:
            self.bone.relative_position = self.target_relative_position
            return

        pos_diff = (
            (self.target_relative_position[0] - self.bone.relative_position[0]),
            (self.target_relative_position[1] - self.bone.relative_position[1]),
        )

        self.bone.relative_position = (
            self.bone.relative_position[0]
            + (pos_diff[0] * self.smoothing_speed["position"] * dt * fps),
            self.bone.relative_position[1]
            + (pos_diff[1] * self.smoothing_speed["position"] * dt * fps),
        )

    def _update_relative_angle_to_target(self, dt):
        if self.target_relative_angle is None:
            return

        if not self.smoothing_enabled["angle"]:
            self.bone.relative_angle = self.target_relative_angle
            return

        angle_diff = (
            self.target_relative_angle - self.bone.relative_angle + 180
        ) % 360 - 180
        self.bone.relative_angle += (
            angle_diff * self.smoothing_speed["angle"] * dt * fps
        )

    def _update_relative_scale_to_target(self, dt):
        if self.target_relative_scale is None:
            return

        if not self.smoothing_enabled["scale"]:
            self.bone.relative_scale = self.target_relative_scale
            return

        scale_diff = (
            self.target_relative_scale[0] - self.bone.relative_scale[0],
            self.target_relative_scale[1] - self.bone.relative_scale[1],
        )
        self.bone.relative_scale = (
            self.bone.relative_scale[0]
            + (scale_diff[0] * self.smoothing_speed["scale"] * dt * fps),
            self.bone.relative_scale[1]
            + (scale_diff[1] * self.smoothing_speed["scale"] * dt * fps),
        )

    def _update_angle_to_target(self, dt):
        if self.target_angle is None:
            return

        if not self.smoothing_enabled["angle"]:
            self.bone.angle = self.target_angle
            return

        angle_diff = (self.target_angle - self.bone.angle + 180) % 360 - 180
        self.bone.angle += angle_diff * self.smoothing_speed["angle"] * dt * fps

    def _update_scale_to_target(self, dt):
        if self.target_scale is None:
            return

        if not self.smoothing_enabled["scale"]:
            self.bone.scale = self.target_scale
            return

        scale_diff = (
            self.target_scale[0] - self.bone.scale[0],
            self.target_scale[1] - self.bone.scale[1],
        )
        self.bone.scale = (
            self.bone.scale[0]
            + (scale_diff[0] * self.smoothing_speed["scale"] * dt * fps),
            self.bone.scale[1]
            + (scale_diff[1] * self.smoothing_speed["scale"] * dt * fps),
        )

    def update(self, dt):
        self._update_relative_position_to_target(dt)
        self._update_relative_angle_to_target(dt)
        self._update_relative_scale_to_target(dt)

        self._update_scale()
        self._update_angle()
        self._update_position()

        self._update_angle_to_target(dt)
        self._update_scale_to_target(dt)

        # Applying temporary smoothing speed
        if self.smoothing_speed_timer["current"] > 0:
            time_percentage = 1 - (
                self.smoothing_speed_timer["current"]
                / self.smoothing_speed_timer["between_animations"]
            )

            def set_smoothing_speed(speed_type: Literal["position", "angle", "scale"]):
                start_speed = self.smoothing_speed["between_animations"][speed_type]
                self.smoothing_speed[speed_type] = (
                    start_speed + (1 - start_speed) * time_percentage
                )

            set_smoothing_speed("position")
            set_smoothing_speed("angle")
            set_smoothing_speed("scale")

            self.smoothing_speed_timer["current"] -= dt
        else:
            self.smoothing_speed_timer["current"] = 0

    def do_default_pose(self):
        self.target_relative_position = (0, 0)
        self.target_relative_angle = 0
        self.target_relative_scale = (1, 1)

    @property
    def target_relative_position(self) -> tuple[float, float] | None:
        return self._target_relative_position

    @target_relative_position.setter
    def target_relative_position(self, value: tuple[float, float] | None):
        self._target_relative_position = value

    @property
    def target_relative_angle(self) -> float | None:
        return self._target_relative_angle

    @target_relative_angle.setter
    def target_relative_angle(self, value: float | None):
        self._target_relative_angle = value

    @property
    def target_relative_scale(self) -> tuple[float, float] | None:
        return self._target_relative_scale

    @target_relative_scale.setter
    def target_relative_scale(self, value: tuple[float, float] | None):
        self._target_relative_scale = value
