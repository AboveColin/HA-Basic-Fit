"""Sensor platform for the Basic-Fit integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import BasicFitDataUpdateCoordinator
from .const import DOMAIN
from .entity import BasicFitEntity


def _latest_measurement(data: dict) -> Any:
    measurements = (data or {}).get("measurements") or []
    return measurements[0] if measurements else None


def _last_visit_time(data: dict) -> datetime | None:
    last = (data.get("stats") or {}).get("last_visit")
    if last is None:
        return None
    raw = last.start_time or last.date
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


@dataclass(frozen=True, kw_only=True)
class BasicFitSensorDescription(SensorEntityDescription):
    """Describes a Basic-Fit sensor and how to read its value."""

    value_fn: Callable[[dict], Any]
    attr_fn: Callable[[dict], dict[str, Any]] | None = None


def _total_visits_attrs(data: dict) -> dict[str, Any]:
    """Extra attributes explaining what the all-time total does (and doesn't) cover."""
    stats = data.get("stats") or {}
    return {
        "earliest_recorded_visit": stats.get("earliest_visit"),
        "note": (
            "Counts every gym visit in Basic-Fit's activity history. This can be "
            "lower than the lifetime total shown in the Basic-Fit app, which also "
            "includes check-ins from before the activity feed started recording them."
        ),
    }


SENSORS: tuple[BasicFitSensorDescription, ...] = (
    BasicFitSensorDescription(
        key="visits_this_month",
        translation_key="visits_this_month",
        icon="mdi:calendar-month",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="visits",
        value_fn=lambda d: (d.get("stats") or {}).get("visits_this_month"),
    ),
    BasicFitSensorDescription(
        key="visits_this_year",
        translation_key="visits_this_year",
        icon="mdi:calendar-star",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="visits",
        value_fn=lambda d: (d.get("stats") or {}).get("visits_this_year"),
    ),
    BasicFitSensorDescription(
        key="visits_total",
        translation_key="visits_total",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="visits",
        value_fn=lambda d: (d.get("stats") or {}).get("visits_total"),
        attr_fn=_total_visits_attrs,
    ),
    BasicFitSensorDescription(
        key="last_visit",
        translation_key="last_visit",
        icon="mdi:dumbbell",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_last_visit_time,
    ),
    BasicFitSensorDescription(
        key="membership_type",
        translation_key="membership_type",
        icon="mdi:card-account-details",
        value_fn=lambda d: getattr(d.get("member"), "membership_type", None),
    ),
    BasicFitSensorDescription(
        key="home_club",
        translation_key="home_club",
        icon="mdi:map-marker",
        value_fn=lambda d: getattr(d.get("member"), "home_club", None),
    ),
    BasicFitSensorDescription(
        key="weight",
        translation_key="weight",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value_fn=lambda d: getattr(_latest_measurement(d), "weight", None),
    ),
    BasicFitSensorDescription(
        key="body_fat",
        translation_key="body_fat",
        icon="mdi:water-percent",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: getattr(_latest_measurement(d), "fat", None),
    ),
    BasicFitSensorDescription(
        key="muscle_mass",
        translation_key="muscle_mass",
        icon="mdi:arm-flex",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value_fn=lambda d: getattr(_latest_measurement(d), "muscle", None),
    ),
    BasicFitSensorDescription(
        key="body_water",
        translation_key="body_water",
        icon="mdi:cup-water",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: getattr(_latest_measurement(d), "water", None),
    ),
    BasicFitSensorDescription(
        key="badges",
        translation_key="badges",
        icon="mdi:trophy",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="badges",
        value_fn=lambda d: len(d.get("badges") or []),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Basic-Fit sensors."""
    coordinator: BasicFitDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    async_add_entities(
        BasicFitSensor(coordinator, config_entry.entry_id, description)
        for description in SENSORS
    )


class BasicFitSensor(BasicFitEntity, SensorEntity):
    """A single Basic-Fit sensor."""

    entity_description: BasicFitSensorDescription

    def __init__(
        self,
        coordinator: BasicFitDataUpdateCoordinator,
        entry_id: str,
        description: BasicFitSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes, if the description defines any."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data or {})
