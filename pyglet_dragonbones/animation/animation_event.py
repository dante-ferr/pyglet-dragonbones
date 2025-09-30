from typing import Callable

class AnimationEvent:
    event_sequence: dict
    event_index: int
    current_duration = 0.0
    total_duration: float

    def __init__(
        self,
        event_sequence: dict,
        event_index=0,
        start_duration=0.0,
    ):
        self.event_sequence = event_sequence
        self.event_index = event_index
        self.total_duration = self._duration_of(event_index)
        self.current_duration = start_duration

    def update(self, frame_step: float, new_event_callback: Callable):
        """Update the animation event's duration and return the next event if the current event is finished."""
        if self.current_duration >= self.total_duration:
            remainder_duration = self.current_duration - self.total_duration
            new_event_index = self._get_next_valid_event_index(
                remainder_duration=remainder_duration
            )

            return new_event_callback(
                event_sequence=self.event_sequence,
                event_index=new_event_index,
                start_duration=remainder_duration + frame_step,
            )

        self._execute_update_changes()
        self.current_duration += frame_step

        return None

    def _execute_update_changes(self):
        raise NotImplementedError

    def _get_next_valid_event_index(
        self, event_index=None, step=1, remainder_duration=0.0
    ):
        """Get the next valid event index, skipping useless events or the ones with a duration smaller than the remainder duration."""
        if event_index is None:
            event_index = self.event_index

        duration_sum = 0

        # Skipping useless events
        while True:
            event_index = self._get_next_event_index(event_index, step)
            new_event_duration = self._duration_of(event_index)
            duration_sum += new_event_duration

            if new_event_duration > 0 and duration_sum > remainder_duration:
                break

        return event_index

    def _get_next_event_index(self, event_index=None, step=1):
        """Get the next event index, handling the case where the event index is out of bounds."""
        if event_index is None:
            event_index = self.event_index

        animation_ended = event_index + step >= len(self.event_sequence)
        if animation_ended:
            return 0
        else:
            return event_index + step

    def _duration_of(self, event_index: int):
        """Get the duration of the event at the given index."""
        return self.event_sequence[event_index].get("duration", 0)

    def _get_info_pair(self):
        """Get the current event and the next event."""
        return (
            self.event_sequence[self.event_index],
            self.event_sequence[self._get_next_event_index()],
        )

    def _index_duration_to_frame(self, index=None, duration=None):
        """Get the corresponding frame for the given index and duration."""
        if index is None:
            index = self.event_index
        if duration is None:
            duration = self.current_duration

        frame = duration
        for i in range(0, index):
            event = self.event_sequence[i]
            frame += event.get("duration", 0)
        return frame
