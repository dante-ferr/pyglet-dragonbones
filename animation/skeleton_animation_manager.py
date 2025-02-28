from typing import TYPE_CHECKING, Literal
from .skeleton_animation import SkeletonAnimation

if TYPE_CHECKING:
    from ..skeleton import Skeleton
    from ..bone import Bone


class SkeletonAnimationManager:
    current_name: str | None = None
    current: SkeletonAnimation | None = None

    def __init__(self, animation_data, skeleton: "Skeleton", framerate: float):
        self.animation_data = animation_data
        self.skeleton = skeleton
        self.framerate = framerate

    def run(self, animation_name: str | None, starting_frame=0, speed=1.0):
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
        )

    def update(self, dt):
        """Update the current animation with the given delta time if it exists."""
        if self.current:
            self.current.update(dt)

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

    # def get_bone_speed(self, bone: "Bone", animation_name: str, frame_range: tuple[int, int], reference: Literal["range", "all"]="all"):
    #     """Calculate the speed of a bone based on its positions in frame_range (x per frame and y per frame). If reference is "range", the speed is calculated relative to the amount of frames in frame_range. If reference is "all", the speed is calculated relative to the total amount of frames in the animation."""
    #     animation_info = self._get_animation_info(animation_name)

    #     x_diff_count = 0
    #     y_diff_count = 0
    #     for frame in range(frame_range[0], frame_range[1]):
    #         x_diff = animation_info["frames"][frame]["position"]["x"] - animation_info["frames"][frame_range[0]]["position"]["x"]
    #         y_diff = animation_info["frames"][frame]["position"]["y"] - animation_info["frames"][frame_range[0]]["position"]["y"]
    #         x_diff_count += x_diff
    #         y_diff_count += y_diff

    #     if reference == "range":
    #         x_diff_count /= frame_range[1] - frame_range[0]
    #         y_diff_count /= frame_range[1] - frame_range[0]
    #     elif reference == "all":
    #         x_diff_count /= len(animation_info["frames"])
