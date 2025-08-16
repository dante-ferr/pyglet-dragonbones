from typing import TYPE_CHECKING, Callable, Literal
from .skeleton_animation import SkeletonAnimation

if TYPE_CHECKING:
    from ..skeleton import Skeleton
    from ..bone import Bone


class SkeletonAnimationManager:
    current_name: str | None = None
    current: SkeletonAnimation | None = None

    def __init__(
        self, animation_data, skeleton: "Skeleton", framerate: float, render: bool
    ):
        self.animation_data = animation_data
        self.skeleton = skeleton
        self.framerate = framerate
        self.render = render

    def run(
        self,
        animation_name: str | None,
        starting_frame=0,
        speed=1.0,
        on_end: Literal["_loop"] | Callable = "_loop",
    ):
        """Change skeleton's animation. If animation_name is None, the skeleton will be reset to its default pose."""
        if self.current_name == animation_name:
            return
        self.current_name = animation_name

        self.skeleton.on_animation_start()

        if animation_name is None:
            self.skeleton._do_default_pose()
            self.current = None
            return

        self.current = SkeletonAnimation(
            info=self._get_animation_info(animation_name),
            skeleton=self.skeleton,
            framerate=self.framerate,
            frame=starting_frame,
            speed=speed,
            on_animation_end=on_end,
        )

        if self.render:
            self.current._instantiate_events(starting_frame)

    def update(self, dt):
        """Updates the animation's internal time counter."""
        if self.current:
            self.current.update(dt)

    def update_visuals(self, dt):
        """Updates the visual components of the current animation."""
        if self.current:
            self.current.update_visuals(dt)

    def set_smooth(self, smooth: bool):
        """Make the current animation smooth or not."""
        if self.current:
            self.current.set_smooth(smooth)
        else:
            raise ValueError("No animation is currently playing.")

    def _get_animation_info(self, animation_name: str):
        """Get the animation info from the animation data, given the animation name."""
        animation_info = next(
            (info for info in self.animation_data if info["name"] == animation_name),
            None,
        )
        if animation_info is None:
            raise ValueError(f"Animation {animation_name} not found.")
        return animation_info
