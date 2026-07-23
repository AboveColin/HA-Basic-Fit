"""Calendar platform for the Basic-Fit integration."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import BasicFitDataUpdateCoordinator
from .const import DOMAIN
from .entity import BasicFitEntity

# Basic-Fit only exposes a check-in time, not a check-out. Show each visit as a
# fixed-length block so it renders as an event rather than an all-day entry.
VISIT_DURATION = timedelta(hours=1)


def _visit_start(visit) -> datetime | None:
    raw = visit.start_time or visit.date
    if not raw:
        return None
    parsed = dt_util.parse_datetime(str(raw))
    if parsed is None:
        day = dt_util.parse_date(str(raw))
        if day is None:
            return None
        parsed = datetime(day.year, day.month, day.day)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return parsed


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Basic-Fit visit calendar."""
    coordinator: BasicFitDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    async_add_entities([BasicFitVisitCalendar(coordinator, config_entry.entry_id)])


class BasicFitVisitCalendar(BasicFitEntity, CalendarEntity):
    """A calendar of gym check-ins."""

    _attr_translation_key = "visits"
    _attr_icon = "mdi:calendar-check"

    def __init__(
        self, coordinator: BasicFitDataUpdateCoordinator, entry_id: str
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator, entry_id, "visit_calendar")

    def _events(self) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for visit in (self.coordinator.data or {}).get("visits") or []:
            start = _visit_start(visit)
            if start is None:
                continue
            events.append(
                CalendarEvent(
                    start=start,
                    end=start + VISIT_DURATION,
                    summary=f"Gym visit — {visit.club}" if visit.club else "Gym visit",
                    location=visit.club,
                )
            )
        events.sort(key=lambda e: e.start)
        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Return the most recent visit as the 'current' event."""
        events = self._events()
        return events[-1] if events else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return visits within the requested window."""
        return [
            event
            for event in self._events()
            if event.start < end_date and event.end > start_date
        ]
