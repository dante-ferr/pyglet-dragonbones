from typing import TYPE_CHECKING

from ._bone_transform import BoneTransform

if TYPE_CHECKING:
    from ..skeleton import Skeleton
    from ..slot import Slot
    from pyglet.graphics import Group


class Bone:
    slots: dict[str, "Slot"]

    def __init__(
        self,
        bone_info,
        parent: "Skeleton | Bone | None" = None,
        group: "Group | None" = None,
    ):
        self.name = bone_info["name"]
        self.group = group

        self._parent = parent

        self._position: tuple[float, float] = (0, 0)
        self._angle: float = 0.0
        self._scale: tuple[float, float] = (1, 1)

        self._relative_position: tuple[float, float] = (0, 0)
        self._relative_angle: float = 0.0
        self._relative_scale: tuple[float, float] = (1, 1)

        self.transform = BoneTransform(bone_info, self)

        self.slots = {}

    @property
    def parent(self):
        if self._parent is None:
            raise ValueError(
                f"Bone {self.name} has no parent. It's necessary to set it as soon as the bone is created."
            )
        return self._parent

    @parent.setter
    def parent(self, value: "Skeleton | Bone | None"):
        self._parent = value

    @property
    def position(self) -> tuple[float, float]:
        return self._position

    @position.setter
    def position(self, value: tuple[float, float]):
        self._position = value

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float):
        self._angle = value

    @property
    def scale(self) -> tuple[float, float]:
        return self._scale

    @scale.setter
    def scale(self, value: tuple[float, float]):
        self._scale = value

    @property
    def relative_position(self) -> tuple[float, float]:
        return self._relative_position

    @relative_position.setter
    def relative_position(self, value: tuple[float, float]):
        """Change bone's relative position."""
        self._relative_position = value

    @property
    def relative_angle(self) -> float:
        return self._relative_angle

    @relative_angle.setter
    def relative_angle(self, value: float):
        """Change bone's relative angle."""
        self._relative_angle = value

    @property
    def relative_scale(self) -> tuple[float, float]:
        return self._relative_scale

    @relative_scale.setter
    def relative_scale(self, value: tuple[float, float]):
        """Change bone's relative scale."""
        self._relative_scale = value

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
        self.transform.set_smoothing(angle, position, scale)

    def on_animation_start(self):
        self.transform.on_animation_start()

    def _update_position(self):
        for slot in self.slots.values():
            slot.update_position()

    def _update_angle(self):
        for slot in self.slots.values():
            slot.update_angle()

    def _update_scale(self):
        for slot in self.slots.values():
            slot.update_scale()

    def update(self, dt):
        self.transform.update(dt)

        self._update_scale()
        self._update_angle()
        self._update_position()

    def do_default_pose(self):
        self.transform.do_default_pose()

        for slot in self.slots.values():
            slot.do_default_pose()
