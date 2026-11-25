"""Shared fixtures for the Basic-Fit tests."""

from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.basic_fit.const import CONF_REFRESH_TOKEN, DOMAIN

SetupIntegration = Callable[[list], Awaitable[MockConfigEntry]]


# Do not make enable_custom_integrations an autouse fixture. It depends on
# `hass`, so an autouse copy runs before a test's own `recorder_mock`, and the
# recorder then starts after `hass` instead of before it. A test that needs the
# recorder lists the fixtures in this order:
#     recorder_mock, enable_custom_integrations, hass
@pytest.fixture
def setup_integration(
    hass: HomeAssistant, enable_custom_integrations: None
) -> SetupIntegration:
    """Return a function that sets up the integration with given measurements."""

    async def _setup(measurements: list) -> MockConfigEntry:
        client = AsyncMock()
        client.get_member.return_value = SimpleNamespace(
            membership_type="Test", home_club="Test club", member_since=None
        )
        client.get_all_visits.return_value = []
        client.get_body_measurements.return_value = measurements
        client.get_badges.return_value = []
        client.get_streak.return_value = None

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="test-member",
            data={CONF_REFRESH_TOKEN: "test-refresh-token"},
        )
        config_entry.add_to_hass(hass)
        with patch(
            "custom_components.basic_fit.BasicFitClient.create", return_value=client
        ):
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
        return config_entry

    return _setup
