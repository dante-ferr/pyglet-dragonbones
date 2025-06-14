from typing import TYPE_CHECKING, TypedDict, cast
from .bone_event import BoneEvent, BoneEventType

if TYPE_CHECKING:
    from .slot_event import SlotEvent, SlotEventType
    from ..skeleton import Skeleton
    from ..slot import Slot

    BoneEventsDict = dict[BoneEventType, BoneEvent]
    SlotEventsDict = dict[SlotEventType, SlotEvent]

    class EventsDict(TypedDict):
        bone: "dict[str, BoneEventsDict]"
        slot: "dict[str, SlotEventsDict]"


class SkeletonAnimation:
    framerate: float
    duration: float
    frame = 0.0
    speed: float
    smooth: bool = True

    events: "EventsDict" = {
        "bone": {},
        "slot": {},
    }

    bone_info: dict
    slot_info: dict

    def __init__(
        self,
        info: dict,
        skeleton: "Skeleton",
        framerate=30.0,
        frame=0,
        speed=1.0,
        paused=False,
    ):
        self.duration = info["duration"]
        self.framerate = framerate
        self.start_frame = frame
        self.bone_info = info["bone"]
        self.slot_info = info["slot"]

        self.skeleton = skeleton
        self.speed = speed

        self._instantiate_events(frame)

        self.playing = not paused

    def set_frame(self, frame: float):
        self._instantiate_events(frame)

    def set_speed(self, speed: float):
        self.speed = speed

    def update(self, dt):
        """Update the current animation with the given delta time if it exists."""
        if not self.playing:
            return

        frame_step = dt * self.speed * self.framerate

        self.set_smooth()
        for bone_events in self.events["bone"].values():
            for event_type, event in bone_events.items():
                new_event = event.update(
                    frame_step,
                    lambda part, event_type, event_sequence, event_index, start_duration: BoneEvent(
                        part, event_type, event_sequence, event_index, start_duration
                    ),
                )
                if new_event:
                    self.events["bone"][event.bone.name][event_type] = new_event

        from .slot_event import SlotEvent

        for slot_events in self.events["slot"].values():
            for event_type, event in slot_events.items():
                new_event = event.update(
                    frame_step,
                    lambda part, event_type, event_sequence, event_index, start_duration: SlotEvent(
                        part,
                        event_type,
                        event_sequence,
                        event_index,
                        start_duration,
                    ),
                )
                if new_event:
                    self.events["slot"][event.slot.name][event_type] = new_event

        self.frame += dt * self.speed

    def set_smooth(self, smooth=None):
        """Make the current animation smooth or not."""
        if smooth is None:
            smooth = self.smooth
        else:
            self.smooth = smooth

        for events in self.events["bone"].values():
            for event in events.values():
                event.smooth = smooth

    def pause(self):
        self.playing = False

    def unpause(self):
        self.playing = True

    def restart(self):
        self._instantiate_events(self.start_frame)

    def _instantiate_events(self, frame: float = 0):
        """Instantiate the events for the given frame."""
        self._instantiate_bone_events(frame)

        self._instantiate_slot_events(frame)

    def _instantiate_bone_events(self, frame: float):
        for bone_animation_info in self.bone_info:
            bone_name = bone_animation_info["name"]
            bone = self.skeleton.bones[bone_name]

            self.events["bone"][bone_name] = {}
            for bone_event_type in BoneEvent.all_event_types:
                if bone_event_type in bone_animation_info:
                    event_sequence = bone_animation_info[bone_event_type]
                    event_index, start_duration = self._frame_to_index_duration(
                        frame, event_sequence
                    )

                    self.events["bone"][bone_name][bone_event_type] = BoneEvent(
                        bone,
                        event_type=bone_event_type,
                        event_sequence=event_sequence,
                        event_index=event_index,
                        start_duration=start_duration,
                    )

    def _instantiate_slot_events(self, frame: float):
        from .slot_event import SlotEvent

        skeleton_slots = cast(
            dict[str, "Slot"], self.skeleton.slots
        )  # This function is only called when render is True. So the skeleton's slots are guaranteed to be of type "Slot".

        for slot_animation_info in self.slot_info:
            slot_name = slot_animation_info["name"]
            slot = skeleton_slots[slot_name]

            self.events["slot"][slot_name] = {}
            for slot_event_type in SlotEvent.all_event_types:
                if slot_event_type in slot_animation_info:
                    event_sequence = slot_animation_info[slot_event_type]
                    event_index, start_duration = self._frame_to_index_duration(
                        frame, event_sequence
                    )

                    self.events["slot"][slot_name][slot_event_type] = SlotEvent(
                        slot,
                        event_type=slot_event_type,
                        event_sequence=event_sequence,
                        event_index=event_index,
                        start_duration=start_duration,
                    )

    def _frame_to_index_duration(self, frame_index: float, event_sequence: dict):
        """Convert a frame index to an event index and duration."""
        if frame_index > self.duration:
            raise ValueError("Frame index is greater than animation duration.")

        i: int = 0
        duration_count: float = 0

        for event in event_sequence:
            if event["duration"] is None:
                raise ValueError(
                    "The animation data contains an event with a duration of None. This is not allowed."
                )
            if event["duration"] <= 0:
                continue
            if duration_count >= frame_index:
                return (i, duration_count - frame_index)

            i += 1
            duration_count += float(event["duration"])

        raise ValueError(
            "The animation does not contain the specified frame index. There may be a problem with the animation data."
        )
