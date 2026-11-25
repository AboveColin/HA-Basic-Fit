"""Check the unit of every body sensor that reads from the latest measurement.

The Basic-Fit API reports fat, muscle and bone as percentages of body weight.
The three values add up to 100. Only weight is in kilograms. The values below
are made up.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import PERCENTAGE, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.basic_fit.const import (
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

MEASUREMENT = SimpleNamespace(
    date="2026-01-01",
    fat=20,
    muscle=75,
    bone=5,
    water=55.5,
    weight=80.5,
)

EXPECTED = {
    "weight": (UnitOfMass.KILOGRAMS, "80.5"),
    "body_fat": (PERCENTAGE, "20"),
    "muscle_mass": (PERCENTAGE, "75"),
    "body_water": (PERCENTAGE, "55.5"),
    "bone_mass": (PERCENTAGE, "5"),
}


@pytest.fixture
async def entry(hass: HomeAssistant) -> MockConfigEntry:
    """Set up the integration with one made-up measurement."""
    client = AsyncMock()
    client.get_member.return_value = SimpleNamespace(
        membership_type="Test", home_club="Test club", member_since=None
    )
    client.get_all_visits.return_value = []
    client.get_body_measurements.return_value = [MEASUREMENT]
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


@pytest.mark.parametrize("key", list(EXPECTED))
async def test_body_sensor_unit(
    hass: HomeAssistant, entry: MockConfigEntry, key: str
) -> None:
    """Each body sensor reports its value in the expected unit."""
    unit, value = EXPECTED[key]
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{key}"
    )
    assert entity_id is not None, f"no sensor registered for {key}"

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["unit_of_measurement"] == unit
    assert state.state == value


async def test_composition_sensors_add_up_to_100(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Fat, muscle and bone are shares of body weight, so they total 100 percent."""
    registry = er.async_get(hass)
    total = 0.0
    for key in ("body_fat", "muscle_mass", "bone_mass"):
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}"
        )
        state = hass.states.get(entity_id)
        assert state.attributes["unit_of_measurement"] == PERCENTAGE
        total += float(state.state)
    assert total == 100
