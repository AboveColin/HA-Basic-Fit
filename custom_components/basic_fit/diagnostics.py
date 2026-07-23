"""Diagnostics support for the Basic-Fit integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "access_token",
    "refresh_token",
    "token",
    "access_expires_at",
    "obtained_at",
    "membership_number",
    "card_number",
    "authorization",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry (tokens and IDs redacted)."""
    data: dict[str, Any] = {
        "entry": {
            "title": config_entry.title,
            "data": async_redact_data(config_entry.data, TO_REDACT),
            "options": async_redact_data(config_entry.options, TO_REDACT),
        },
    }

    if config_entry.entry_id not in hass.data.get(DOMAIN, {}):
        data["error"] = "Integration not initialized"
        return data

    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = domain_data.get("coordinator")

    if coordinator:
        info: dict[str, Any] = {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        }
        if coordinator.data:
            member = coordinator.data.get("member")
            stats = coordinator.data.get("stats") or {}
            info["data_summary"] = {
                "membership_type": getattr(member, "membership_type", None),
                "home_club": getattr(member, "home_club", None),
                "visits_total": stats.get("visits_total"),
                "visits_this_month": stats.get("visits_this_month"),
                "visits_this_year": stats.get("visits_this_year"),
                "measurements_count": len(coordinator.data.get("measurements") or []),
                "badges_count": len(coordinator.data.get("badges") or []),
            }
        data["coordinator"] = info

    return data
