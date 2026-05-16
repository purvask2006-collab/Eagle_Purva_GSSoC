from __future__ import annotations

from time import monotonic

from libs.schemas.tracking import TrackLifecycleEvent
from libs.config.settings import settings


_reasoning_cooldowns: dict[int, float] = {}

SUSPICIOUS_ACTIONS = {
    "LINGERING",
    "NEAR_KEYPAD",
    "REPEATED_APPROACH",
}


def reset_cooldown(track_id: int) -> None:
    """Clear cooldown state after reasoning completes."""
    _reasoning_cooldowns.pop(track_id, None)


def should_trigger_reasoning(
    event: TrackLifecycleEvent,
    suspicious_actions: set[str],
) -> bool:
    """Determine whether VLM/LLM reasoning should be triggered."""

    # Must be inside at least one restricted zone
    if not event.zones_present:
        return False

    # Dwell time must exceed configured threshold
    if (
        event.dwell_time_seconds
        < settings.reasoning_dwell_threshold_seconds
    ):
        return False

    # At least one suspicious action must exist
    if not (SUSPICIOUS_ACTIONS & suspicious_actions):
        return False

    now = monotonic()

    # Cooldown protection
    last_trigger = _reasoning_cooldowns.get(event.track_id)

    if (
        last_trigger is not None
        and (
            now - last_trigger
            < settings.reasoning_cooldown_seconds
        )
    ):
        return False

    # Store latest trigger timestamp
    _reasoning_cooldowns[event.track_id] = now

    return True