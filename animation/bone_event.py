from typing import Literal, Callable
from .animation_event import AnimationEvent
from ..bone import Bone

BoneEventType = Literal["translateFrame", "rotateFrame", "scaleFrame"]


class BoneEvent(AnimationEvent):
    skeleton_part_type = "bone"
    bone: Bone
    all_event_types: list[BoneEventType] = [
        "translateFrame",
        "rotateFrame",
        "scaleFrame",
    ]
    event_type: BoneEventType

    smooth: bool = True

    def __init__(
        self,
        bone: Bone,
        event_type: BoneEventType,
        event_sequence: dict,
        event_index=0,
        start_duration=0,
    ):
        super().__init__(event_sequence, event_index, start_duration)
        self.bone = bone
        self.event_type = event_type

    def update(self, frame_step: float, new_event_callback: Callable):
        """Update the event with the given frame step and new event callback."""
        return super().update(
            frame_step,
            lambda event_sequence, event_index, start_duration: new_event_callback(
                self.bone, self.event_type, event_sequence, event_index, start_duration
            ),
        )

    def _execute_update_changes(self):
        """Execute the update changes of the event."""
        info = self._get_info_pair()

        if self.event_type == "translateFrame":
            key_x = (info[0].get("x", 0), info[1].get("x", 0))
            key_y = (info[0].get("y", 0), info[1].get("y", 0))

            x = key_x[0] + (
                (key_x[1] - key_x[0]) * self.current_duration / self.total_duration
                if self.smooth
                else 0
            )
            y = key_y[0] + (
                (key_y[1] - key_y[0]) * self.current_duration / self.total_duration
                if self.smooth
                else 0
            )
            self.bone.set_target_position(x, y)

        elif self.event_type == "rotateFrame":
            key_angle = (-info[0].get("rotate", 0), -info[1].get("rotate", 0))

            angle = key_angle[0] + (
                (key_angle[1] - key_angle[0])
                * self.current_duration
                / self.total_duration
                if self.smooth
                else 0
            )
            self.bone.set_target_angle(angle)

        elif self.event_type == "scaleFrame":
            key_x = (info[0].get("x", 1), info[1].get("x", 1))
            key_y = (info[0].get("y", 1), info[1].get("y", 1))

            x = key_x[0] + (
                (key_x[1] - key_x[0]) * self.current_duration / self.total_duration
                if self.smooth
                else 0
            )
            y = key_y[0] + (
                (key_y[1] - key_y[0]) * self.current_duration / self.total_duration
                if self.smooth
                else 0
            )
            self.bone.set_target_scale(x, y)
