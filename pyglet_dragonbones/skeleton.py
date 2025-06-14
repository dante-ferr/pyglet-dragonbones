import json
from .bone import Bone
from .animation.skeleton_animation import SkeletonAnimation
import os
import pyglet
from .animation.skeleton_animation_manager import SkeletonAnimationManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics import Group


class Skeleton:
    current_animation_name: str | None = None
    current_animation: SkeletonAnimation | None = None
    frame = 0
    framerate: float

    bones: dict[str, Bone]

    animation_data: list[dict]

    target_angle: float | None = None

    animation_manager: SkeletonAnimationManager

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

        self._load_structure()

        self.set_position(0, 0)
        self.set_scale(1, 1)
        self.set_angle(0)

        if self.render:
            self.animation_manager = self._get_animation_manager()

    def _get_skeleton_data(self, skeleton_path: str):
        with open(f"{skeleton_path}/{self.entity_name}_ske.json", "r") as file:
            return json.load(file)

    def _load_structure(self):
        self.bones = self._load_bones()
        if self.render:
            from .get_subtextures import get_subtextures

            subtextures = get_subtextures(
                f"{self.skeleton_path}/{self.entity_name}_tex.json",
                f"{self.skeleton_path}/{self.entity_name}_tex.png",
            )
            self.slots = self._load_slots(
                (self.armature_data["slot"], self.armature_data["skin"][0]["slot"]),
                subtextures=subtextures,
            )

    def _get_animation_manager(self):
        animation_data = self.armature_data["animation"]
        framerate = self.skeleton_data["frameRate"]
        return SkeletonAnimationManager(animation_data, self, framerate)

    def _load_bones(self):
        data = self.armature_data["bone"]
        bones: dict[str, Bone] = {}

        for b in data:
            bone_name = b["name"]
            bone_group = self.groups.get(bone_name) if self.groups else None

            bone = Bone(b, self, bone_group)
            bones[bone_name] = bone

        return bones

    def _load_slots(self, data, subtextures):
        from .slot import Slot

        slots: dict[str, Slot] = {}

        slot_data, skin_data = data
        # Iterate through armature slots
        for slot_info in slot_data:
            slot_displays = None

            # Find matching slot in skin and retrieve display info
            for slot in skin_data:
                if slot["name"] == slot_info["name"]:
                    slot_displays = slot.get("display")  # Use .get() to avoid KeyError
                    break

            # If slot displays are found, create a dictionary for subtextures
            slot_subtextures = {}
            if slot_displays:
                slot_subtextures = [
                    subtextures[display["name"]] for display in slot_displays
                ]
            else:
                return

            # Create a slot and assign it to the bone's slot dictionary
            bone_name = slot_info["parent"]
            slot_name = slot_info["name"]

            bone = self.bones[bone_name]
            slot = Slot(
                slot_info, bone=bone, subtextures=slot_subtextures, batch=self.batch
            )
            slots[slot_name] = slot

        return slots

    def set_position(self, x: float, y: float):
        """Change skeleton's position."""
        self.position = (x, y)

    def set_angle(self, angle: float):
        """Change skeleton's angle."""
        self.angle = angle

    def set_scale(self, x: float, y: float):
        """Change skeleton's scale."""
        self.scale = (x, y)

    def set_target_angle(self, angle: float):
        self.target_angle = angle

    def _do_default_pose(self):
        for bone in self.bones.values():
            bone.do_default_pose()

    def on_animation_start(self):
        for bone in self.bones.values():
            bone.on_animation_start()

    def run_animation(self, animation_name: str | None, starting_frame=0, speed=1):
        if self.render:
            self.animation_manager.run(animation_name, starting_frame, speed)

    def update(self, dt):
        """Update skeleton's attributes and draw each of its parts."""
        for bone in self.bones.values():
            bone.update(dt)

        if self.render:
            self.animation_manager.update(dt)

        if self.render:
            self.batch.draw()

    def update_angle_to_target(self, dt):
        if self.target_angle is not None:
            angle_diff = (self.target_angle - self.angle + 180) % 360 - 180
            self.angle += angle_diff * self.angle_smoothing_speed * dt

            self.set_angle(self.angle)
