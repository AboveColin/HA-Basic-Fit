"""Binary sensor platform for the Basic-Fit integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BasicFitDataUpdateCoordinator
from .const import DOMAIN
from .entity import BasicFitEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Basic-Fit binary sensors."""
    coordinator: BasicFitDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    async_add_entities([BasicFitDebtBinarySensor(coordinator, config_entry.entry_id)])


class BasicFitDebtBinarySensor(BasicFitEntity, BinarySensorEntity):
    """Reports whether the membership has an outstanding balance."""

    _attr_translation_key = "has_debt"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: BasicFitDataUpdateCoordinator, entry_id: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry_id, "has_debt")

    @property
    def is_on(self) -> bool | None:
        """Return True if the account has outstanding debt."""
        member = self._member
        if member is None:
            return None
        return bool(getattr(member, "has_debt", None))
