"""Base entity for the Basic-Fit integration."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BasicFitDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER


class BasicFitEntity(CoordinatorEntity[BasicFitDataUpdateCoordinator]):
    """Base entity tying platform entities to the membership device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: BasicFitDataUpdateCoordinator, entry_id: str, key: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}"

    @property
    def _member(self):
        """Return the current membership summary (may be ``None``)."""
        return (self.coordinator.data or {}).get("member")

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device that all Basic-Fit entities hang off."""
        member = self._member
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Basic-Fit",
            manufacturer=MANUFACTURER,
            model=getattr(member, "membership_type", None) or "Membership",
        )

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success
