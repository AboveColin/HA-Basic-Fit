"""System health for the Basic-Fit integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN


@callback
def async_register(
    hass: HomeAssistant, register: Any  # type: ignore[type-arg]
) -> None:
    """Register system health callbacks."""
    register.async_register_info(async_check_api_health)


async def async_check_api_health(hass: HomeAssistant) -> dict[str, Any]:
    """Report whether the Basic-Fit account(s) are being polled successfully."""
    data: dict[str, Any] = {}

    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        data["status"] = "not_configured"
        return data

    healthy = 0
    total = len(entries)
    for entry in entries:
        if entry.entry_id not in hass.data.get(DOMAIN, {}):
            continue
        coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
        if coordinator and coordinator.last_update_success:
            healthy += 1

    data["status"] = "ok" if healthy == total else "error"
    data["configured_accounts"] = total
    data["healthy_accounts"] = healthy
    if healthy < total:
        data["error"] = f"{total - healthy} of {total} accounts are not responding"
    return data
