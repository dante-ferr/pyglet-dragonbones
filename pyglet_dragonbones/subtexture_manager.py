from PIL import Image
import json
import math
import numpy as np
import matplotlib.pyplot as plt
import pyglet
from functools import cached_property, lru_cache
from typing import Any, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .skeleton import Skeleton


class TextureFrame(TypedDict):
    frame_width: int
    frame_height: int
    frame_x: int
    frame_y: int


class Subtexture(TypedDict):
    name: str
    angle: float
    image: pyglet.image.AbstractImage


class SubtextureManager:
    def __init__(self, skeleton: "Skeleton"):
        self.skeleton = skeleton

    @cached_property
    def subtextures(self) -> dict[str, Subtexture]:
        texture_path = (
            f"{self.skeleton.skeleton_path}/{self.skeleton.entity_name}_tex.json"
        )

        with open(texture_path, "r") as file:
            texture_data = json.load(file)

        subtextures: dict[str, Subtexture] = {}
        for subtexture_data in texture_data["SubTexture"]:
            name = subtexture_data["name"]
            subtextures[name] = self._process_subtexture(subtexture_data)

        return subtextures

    def _process_subtexture(self, subtexture_data: dict[str, Any]) -> Subtexture:
        """Processes a single subtexture entry from the texture atlas data."""
        name = subtexture_data["name"]
        height = subtexture_data.get("height", 0)
        texture_frame = TextureFrame(
            frame_width=subtexture_data.get("frameWidth", 0),
            frame_height=subtexture_data.get("frameHeight", 0),
            frame_x=subtexture_data.get("frameX", 0),
            frame_y=subtexture_data.get("frameY", 0),
        )

        x_transform, y_transform, skX_degrees = self._get_transforms(name)

        image = self._create_pyglet_image(
            subtexture_data, x_transform, y_transform, texture_frame
        )

        if name == "feather1":
            middle_x = texture_frame["frame_width"] // 2 + texture_frame["frame_x"]
            middle_y = height - (
                texture_frame["frame_height"] // 2 + texture_frame["frame_y"]
            )

        return Subtexture(name=name, angle=skX_degrees, image=image)

    def _get_transforms(self, name: str) -> tuple[float, float, float]:
        """Calculates the final x, y, and angle transforms for a subtexture."""
        skin_transform = self.slot_skin_transforms.get(name, {})
        bone_transform = self.bone_transforms.get(self.display_bone_dict[name], {})

        x_transform = skin_transform.get("x", 0)
        y_transform = skin_transform.get("y", 0)
        skX_degrees = -bone_transform.get("skX", 0)

        if skX_degrees != 0:
            angle_radians = math.radians(skX_degrees)
            cos_angle = math.cos(angle_radians)
            sin_angle = math.sin(angle_radians)
            x_rotated = x_transform * cos_angle - y_transform * sin_angle
            y_rotated = x_transform * sin_angle + y_transform * cos_angle

            x_transform, y_transform = x_rotated, y_rotated

        return x_transform, y_transform, skX_degrees

    def _create_pyglet_image(
        self,
        subtexture_data: dict[str, Any],
        x_transform: float,
        y_transform: float,
        texture_frame: TextureFrame,
    ) -> pyglet.image.AbstractImage:
        """Crops the subtexture from the atlas and creates a pyglet image with the correct anchor."""
        x, y = subtexture_data["x"], subtexture_data["y"]
        width, height = subtexture_data["width"], subtexture_data["height"]

        cropped_image = self.atlas_image.crop((x, y, x + width, y + height))

        # if subtexture_data["name"] == "feather1":
        #     image_bytes = cropped_image.tobytes()
        #     # The format is 'RGBA', so each pixel has 4 bytes (R, G, B, A)
        #     image_array = np.frombuffer(image_bytes, dtype=np.uint8).reshape(
        #         (height, width, 4)
        #     )
        #     plt.imshow(image_array)
        #     plt.title(f"Plot for subtexture: {subtexture_data['name']}")
        #     plt.show()

        image = pyglet.image.ImageData(width, height, "RGBA", cropped_image.tobytes())

        middle_x = texture_frame["frame_width"] // 2 + texture_frame["frame_x"]
        # middle_y = height - (
        #     texture_frame["frame_height"] // 2 + texture_frame["frame_y"]
        # )
        middle_y = texture_frame["frame_height"] // 2 + texture_frame["frame_y"]

        image.anchor_x = round(middle_x - x_transform)
        image.anchor_y = round(middle_y + y_transform)
        return image

    @lru_cache(maxsize=1)
    def _get_atlas_image(self) -> Image.Image:
        """Loads the texture atlas image from disk."""
        image_path = (
            f"{self.skeleton.skeleton_path}/{self.skeleton.entity_name}_tex.png"
        )
        return Image.open(image_path)

    @property
    def atlas_image(self) -> Image.Image:
        return self._get_atlas_image()

    @cached_property
    def display_bone_dict(self) -> dict[str, str]:
        """A dictionary mapping display names to their parent bone names."""
        display_bone_dict: dict[str, str] = {}
        for skin_slot in self.skeleton.armature_data["skin"][0]["slot"]:
            slot_name = skin_slot["name"]
            bone_name = self.slot_bone_dict.get(slot_name)
            if bone_name:
                for display in skin_slot.get("display", []):
                    display_bone_dict[display["name"]] = bone_name
        return display_bone_dict

    @cached_property
    def slot_bone_dict(self) -> dict[str, str]:
        """A dictionary mapping slot names to their parent bone names."""
        slot_bone_dict: dict[str, str] = {}
        for slot in self.skeleton.armature_data["slot"]:
            slot_bone_dict[slot["name"]] = slot["parent"]
        return slot_bone_dict

    @cached_property
    def slot_skin_transforms(self) -> dict[str, Any]:
        """A dictionary mapping display names to their transforms from the skin data."""
        slot_skin_transforms: dict[str, Any] = {}
        for skin_slot in self.skeleton.armature_data["skin"][0]["slot"]:
            for display in skin_slot.get("display", []):
                if "transform" in display:
                    slot_skin_transforms[display["name"]] = display["transform"]
        return slot_skin_transforms

    @cached_property
    def bone_transforms(self) -> dict[str, Any]:
        """A dictionary mapping bone names to their base transforms."""
        bone_transforms: dict[str, Any] = {}
        for bone in self.skeleton.armature_data["bone"]:
            if "transform" in bone:
                bone_transforms[bone["name"]] = bone["transform"]
        return bone_transforms
