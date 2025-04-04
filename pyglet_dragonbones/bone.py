import json
from .slot import Slot
import pyglet
from typing import TYPE_CHECKING, TypedDict, Literal
import math
from .config import config

if TYPE_CHECKING:
    from .skeleton import Skeleton

fps = config.fps
global_scale = config.global_scale


class BetweenAnimationsType(TypedDict):
    angle: float
    position: float
    scale: float


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


class Bone:
    slots: dict[str, Slot]

    base_position: tuple[float, float]
    base_angle = 0.0
    base_scale: tuple[float, float]

    position: tuple[float, float]
    angle = 0.0
    scale: tuple[float, float]

    relative_position: tuple[float, float]
    relative_angle = 0.0
    relative_scale: tuple[float, float]

    target_relative_position: tuple[float, float] | None = None
    target_relative_angle: float | None = None
    target_relative_scale: tuple[float, float] | None = None

    def __init__(
        self,
        bone_info,
        skeleton: "Skeleton",
        group: pyglet.graphics.Group | None = None,
    ):
        self.name = bone_info["name"]
        self.group = group
        # self.parent = bone_info['parent']
        self.skeleton = skeleton

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

        self.smoothing_speed_timer = {
            "between_animations": 5,
            "current": 0,
        }
        self.smoothing_speed: SmoothingSpeedType = {
            "between_animations": {
                "angle": 0.3,
                "position": 0.3,
                "scale": 0.3,
            },
            "angle": 1,
            "position": 1,
            "scale": 1,
        }

        self.position = (0, 0)
        self.angle = 0
        self.scale = (1, 1)

        self.set_position(0, 0)
        self.set_angle(0)
        self.set_scale(1, 1)

        self.slots = {}

    # def set_parent(self):
    #     if self.parent:
    #         self.parent = self.skeleton.bones[self.parent]

    def set_position(self, x: float, y: float):
        """Change bone's relative position."""
        self.relative_position = (
            x,
            y,
        )

    def set_angle(self, angle: float):
        """Change bone's relative angle."""
        self.relative_angle = angle

    def set_scale(self, x: float, y: float):
        """Change bone's relative scale."""
        self.relative_scale = (x, y)

    def set_target_position(self, x: float, y: float):
        self.target_relative_position = (x, y)

    def set_target_angle(self, angle: float):
        self.target_relative_angle = angle

    def set_target_scale(self, x: float, y: float):
        self.target_relative_scale = (x, y)

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
            self.relative_position[0] + self.base_position[0],
            self.relative_position[1] + self.base_position[1],
        )
        scaled_position = (
            anchored_position[0] * self.skeleton.scale[0],
            anchored_position[1] * self.skeleton.scale[1],
        )
        rotated_position = rotate_position(scaled_position, self.angle)
        self.position = (
            self.skeleton.position[0] + rotated_position[0],
            self.skeleton.position[1] + rotated_position[1],
        )

        for slot in self.slots.values():
            slot.update_position()

    def _update_angle(self):
        anchored_angle = self.relative_angle + self.base_angle
        self.angle = self.skeleton.angle + anchored_angle

        for slot in self.slots.values():
            slot.update_angle()

    def _update_scale(self):
        anchored_scale = (
            self.relative_scale[0] * self.base_scale[0],
            self.relative_scale[1] * self.base_scale[1],
        )
        self.scale = (
            self.skeleton.scale[0] * anchored_scale[0],
            self.skeleton.scale[1] * anchored_scale[1],
        )

        for slot in self.slots.values():
            slot.update_scale()

    def _update_position_to_target(self, dt):
        if self.target_relative_position is None:
            return

        pos_diff = (
            (self.target_relative_position[0] - self.relative_position[0]),
            (self.target_relative_position[1] - self.relative_position[1]),
        )

        self.set_position(
            self.relative_position[0]
            + (pos_diff[0] * self.smoothing_speed["position"] * dt * fps),
            self.relative_position[1]
            + (pos_diff[1] * self.smoothing_speed["position"] * dt * fps),
        )

    def _update_angle_to_target(self, dt):
        if self.target_relative_angle is None:
            return

        angle_diff = (
            self.target_relative_angle - self.relative_angle + 180
        ) % 360 - 180
        self.set_angle(
            self.relative_angle + angle_diff * self.smoothing_speed["angle"] * dt * fps
        )

    def _update_scale_to_target(self, dt):
        if self.target_relative_scale is None:
            return

        scale_diff = (
            self.target_relative_scale[0] - self.relative_scale[0],
            self.target_relative_scale[1] - self.relative_scale[1],
        )
        self.set_scale(
            self.relative_scale[0]
            + (scale_diff[0] * self.smoothing_speed["scale"] * dt * fps),
            self.relative_scale[1]
            + (scale_diff[1] * self.smoothing_speed["scale"] * dt * fps),
        )

    def update(self, dt):
        self._update_position_to_target(dt)
        self._update_angle_to_target(dt)
        self._update_scale_to_target(dt)

        self._update_scale()
        self._update_angle()
        self._update_position()

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
        self.set_target_position(0, 0)
        self.set_target_angle(0)
        self.set_target_scale(1, 1)

        for slot in self.slots.values():
            slot.do_default_pose()
