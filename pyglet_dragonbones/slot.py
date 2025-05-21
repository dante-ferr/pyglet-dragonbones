import pyglet
from .get_subtextures import Subtexture
from typing import TYPE_CHECKING
from .utils import refine_texture

if TYPE_CHECKING:
    from .bone import Bone


class Slot:
    current_display: int

    def __init__(
        self,
        slot_info,
        bone: "Bone",
        subtextures: list[Subtexture],
        batch: pyglet.graphics.Batch,
    ):
        self.bone = bone
        self.name = slot_info["name"]
        self.subtextures = subtextures
        self.group = bone.group

        self.relative_position = (0.0, 0.0)
        self.relative_angle = 0.0
        self.relative_scale = (1.0, 1.0)

        self.default_display = slot_info.get("displayIndex", 1) - 1
        self.current_display = self.default_display
        default_texture = self._get_texture_from_image(
            self.subtextures[self.default_display]["image"]
        )

        self.sprite = pyglet.sprite.Sprite(
            default_texture, group=self.group, batch=batch
        )

        self.bone.slots[self.name] = self

    def change_display(self, display_index: int):
        """Change the sprite's texture."""
        self.current_display = display_index

        self.sprite.image = self._get_texture_from_image(
            self.subtextures[display_index]["image"]
        )

    def _get_texture_from_image(self, image: pyglet.image.AbstractImage):
        """Change the sprite's texture."""
        texture = image.get_texture()
        refine_texture()
        return texture

    def do_default_pose(self):
        self.change_display(self.default_display)

    def update_position(self):
        """Follow parent bone's position"""
        self.sprite.x = self.bone.position[0] + self.relative_position[0]
        self.sprite.y = self.bone.position[1] + self.relative_position[1]

    def update_angle(self):
        """Follow parent bone's angle"""
        self.sprite.rotation = self.bone.angle + self.relative_angle

    def update_scale(self):
        """Follow parent bone's scale"""
        self.sprite.scale_x = self.bone.scale[0] * self.relative_scale[0]
        self.sprite.scale_y = self.bone.scale[1] * self.relative_scale[1]
