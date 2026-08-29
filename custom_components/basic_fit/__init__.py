"""The Basic-Fit integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

try:
    from basicfit import BasicFitClient, TokenSet
    from basicfit.exceptions import BasicFitAuthError, BasicFitError
except ImportError as err:  # pragma: no cover - handled by manifest requirements
    _LOGGER.error("Failed to import the basicfit package: %s", err)
    raise

from .const import (
    CONF_ACCESS_EXPIRES_AT,
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_OBTAINED_AT,
    CONF_REDIRECT_URI,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
]

SCAN_INTERVAL = timedelta(minutes=30)


def tokens_from_entry(entry: ConfigEntry) -> TokenSet:
    """Rebuild a :class:`TokenSet` from stored config-entry data."""
    data = entry.data
    return TokenSet(
        refresh_token=data[CONF_REFRESH_TOKEN],
        access_token=data.get(CONF_ACCESS_TOKEN),
        access_expires_at=data.get(CONF_ACCESS_EXPIRES_AT),
        client_id=data.get(CONF_CLIENT_ID),
        redirect_uri=data.get(CONF_REDIRECT_URI),
        obtained_at=data.get(CONF_OBTAINED_AT),
    )


class BasicFitDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator that polls the Basic-Fit account for a single membership."""

    def __init__(self, hass: HomeAssistant, client: BasicFitClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch membership, visits, measurements and badges."""
        try:
            member = await self.client.get_member()
            visits = await self.client.get_all_visits()
            try:
                measurements = await self.client.get_body_measurements()
            except BasicFitError as err:
                _LOGGER.debug("Body measurements unavailable: %s", err)
                measurements = []
            try:
                badges = await self.client.get_badges()
            except BasicFitError as err:
                _LOGGER.debug("Badges unavailable: %s", err)
                badges = []
            try:
                streak = await self.client.get_streak()
            except BasicFitError as err:
                _LOGGER.debug("Streak unavailable: %s", err)
                streak = None
        except BasicFitAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BasicFitError as err:
            raise UpdateFailed(f"Error communicating with Basic-Fit: {err}") from err

        return {
            "member": member,
            "visits": visits,
            "measurements": measurements,
            "badges": badges,
            "streak": streak,
            "stats": _visit_stats(visits),
        }


def _visit_stats(visits: list) -> dict:
    """Derive convenience counters from the gym-visit list."""
    # dt_util.now() honours Home Assistant's configured timezone; date.today()
    # would use the host's, so "this month" would roll over at the wrong hour.
    today = dt_util.now().date()
    month_prefix = today.strftime("%Y-%m")
    year_prefix = today.strftime("%Y")
    this_month = sum(1 for v in visits if str(v.date or "").startswith(month_prefix))
    this_year = sum(1 for v in visits if str(v.date or "").startswith(year_prefix))
    dates = sorted(str(v.date) for v in visits if v.date)
    return {
        "visits_total": len(visits),
        "visits_this_month": this_month,
        "visits_this_year": this_year,
        "last_visit": visits[0] if visits else None,
        "earliest_visit": dates[0] if dates else None,
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Basic-Fit from a config entry."""
    session = async_get_clientsession(hass)

    def save_tokens(tokens: TokenSet) -> None:
        """Persist the rotated token set back onto the config entry."""
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_REFRESH_TOKEN: tokens.refresh_token,
                CONF_ACCESS_TOKEN: tokens.access_token,
                CONF_ACCESS_EXPIRES_AT: tokens.access_expires_at,
                CONF_CLIENT_ID: tokens.client_id,
                CONF_REDIRECT_URI: tokens.redirect_uri,
                CONF_OBTAINED_AT: tokens.obtained_at,
            },
        )

    client = BasicFitClient.create(
        tokens_from_entry(entry),
        session=session,
        token_updated=save_tokens,
    )

    coordinator = BasicFitDataUpdateCoordinator(hass, client)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except UpdateFailed as err:
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
