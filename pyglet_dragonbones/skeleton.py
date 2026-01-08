import json
import os
import pyglet
from .animation.skeleton_animation_manager import SkeletonAnimationManager
from .skeleton_structure_manager import SkeletonStructureManager
from typing import TYPE_CHECKING, Literal, Callable

if TYPE_CHECKING:
    from pyglet.graphics import Group
    from .bone import Bone
    from .slot import Slot


class Skeleton:
    bones: dict[str, "Bone"]
    slots: dict[str, "Slot"] | None

    _position: tuple[float, float]
    _angle: float
    _scale: tuple[float, float]

    _target_angle: float | None = None

    def __init__(
        self,
        skeleton_path: str,
        groups: dict[str, "Group"] | None = None,
        angle_smoothing_speed=10.0,
        render=True,
    ):
        """
        Load a skeleton from a JSON file and create bones and slots.

        Parameters:
        - skeleton_path: The path to the folder containing the skeleton data. The folder should be named similarly to your DragonBones project and must contain the following files:
            - <db project name>_ske.json: The skeleton data in JSON format.
            - <db project name>.json: The subtexture data in JSON format.
            - <db project name>.png: The subtexture image.
        - groups: A dictionary mapping pyglet groups. Each group corresponds to a bone in your DragonBones project and must have the same name as its associated bone. Bones without a corresponding group will be assigned to the skeleton's base group by default. Setting "render" to False makes the groups unnecessary, so if this is the case you should pass None to this parameter or omit it.
        - angle_smoothing_speed: The speed at which the angle of the skeleton is approached to the target angle.
        - render: A boolean indicating whether to render the skeleton. Setting it to False prevents xlib related errors on environments without displays.
        """
        self.groups = groups
        self.render = render
        self.angle_smoothing_speed = angle_smoothing_speed

        self.skeleton_path = skeleton_path
        self.entity_name = os.path.basename(skeleton_path)
        self.skeleton_data = self._get_skeleton_data(skeleton_path)

        self.armature_data = self.skeleton_data["armature"][0]

        if render:
            self.batch = pyglet.graphics.Batch()

        structure_manager = SkeletonStructureManager(self)
        self.bones = structure_manager.bones
        self.slots = structure_manager.slots

        self.position = (0, 0)
        self.scale = (1, 1)
        self.angle = 0

        self.animation_manager = self._get_animation_manager()

    def _get_skeleton_data(self, skeleton_path: str):
        with open(f"{skeleton_path}/{self.entity_name}_ske.json", "r") as file:
            return json.load(file)

    def _get_animation_manager(self):
        animation_data = self.armature_data["animation"]
        framerate = self.skeleton_data["frameRate"]
        return SkeletonAnimationManager(
            animation_data, self, framerate, render=self.render
        )

    @property
    def position(self) -> tuple[float, float]:
        return self._position

    @position.setter
    def position(self, value: tuple[float, float]):
        """Change skeleton's position."""
        self._position = value

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float):
        """Change skeleton's angle."""
        self._angle = value

    @property
    def scale(self) -> tuple[float, float]:
        return self._scale

    @scale.setter
    def scale(self, value: tuple[float, float]):
        """Change skeleton's scale."""
        self._scale = value

    @property
    def target_angle(self) -> float | None:
        return self._target_angle

    @target_angle.setter
    def target_angle(self, value: float | None):
        self._target_angle = value

    def do_default_pose(self):
        for bone in self.bones.values():
            bone.do_default_pose()

    def on_animation_start(self):
        # Every time we run a new animation, reset the skeleton to its default pose. That's necessary because some animations might not affect all
        # bones, and we don't want the previous animation's pose to affect the new one.
        self.do_default_pose()

        for bone in self.bones.values():
            bone.on_animation_start()

    def run_animation(
        self,
        animation_name: str | None,
        starting_frame=0,
        speed=1,
        on_end: Literal["_loop"] | Callable = "_loop",
    ):
        self.animation_manager.run(animation_name, starting_frame, speed, on_end)

    def update(self, dt):
        """
        Updates the skeleton. The logic part always runs, the visual part is optional.
        """
        self.animation_manager.update(dt)
        self.update_angle_to_target(dt)

        if self.render:
            self.animation_manager.update_visuals(dt)
            for bone in self.bones.values():
                bone.update(dt)

    def draw(self, dt):
        self.batch.draw()

    def update_angle_to_target(self, dt):
        if self._target_angle is not None:
            angle_diff = (self._target_angle - self.angle + 180) % 360 - 180
            self.angle += angle_diff * self.angle_smoothing_speed * dt

    @property
    def current_animation_name(self):
        return self.animation_manager.current_name
