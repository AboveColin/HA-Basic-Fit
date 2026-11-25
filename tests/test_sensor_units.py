"""Check the unit and the source of the body sensors.

The Basic-Fit API reports fat, muscle and bone as percentages of body weight.
Only weight is in kilograms. All values below are made up.
"""

from types import SimpleNamespace

import pytest
from homeassistant.const import PERCENTAGE, STATE_UNKNOWN, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.basic_fit.const import DOMAIN

from .conftest import SetupIntegration

NEWEST = SimpleNamespace(
    date="2026-02-01", fat=20, muscle=75, bone=5, water=55.5, weight=80.5
)
OLDER = SimpleNamespace(
    date="2026-01-01", fat=30, muscle=65, bone=4, water=45.5, weight=90.5
)

# sensor key: (unit, state for NEWEST)
EXPECTED = {
    "weight": (UnitOfMass.KILOGRAMS, "80.5"),
    "body_fat": (PERCENTAGE, "20"),
    "muscle_mass": (PERCENTAGE, "75"),
    "body_water": (PERCENTAGE, "55.5"),
    "bone_mass": (PERCENTAGE, "5"),
}


def _state(hass: HomeAssistant, entry_id: str, key: str):
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry_id}_{key}"
    )
    assert entity_id is not None, f"no sensor registered for {key}"
    state = hass.states.get(entity_id)
    assert state is not None
    return state


@pytest.mark.parametrize("key", list(EXPECTED))
async def test_body_sensor_unit_and_value(
    hass: HomeAssistant, setup_integration: SetupIntegration, key: str
) -> None:
    """Each body sensor reports its value in the expected unit."""
    entry = await setup_integration([NEWEST])
    unit, value = EXPECTED[key]

    state = _state(hass, entry.entry_id, key)
    assert state.attributes["unit_of_measurement"] == unit
    assert state.state == value


@pytest.mark.parametrize("key", list(EXPECTED))
async def test_body_sensors_read_the_first_measurement(
    hass: HomeAssistant, setup_integration: SetupIntegration, key: str
) -> None:
    """The API lists the newest measurement first. Older ones are ignored."""
    entry = await setup_integration([NEWEST, OLDER])

    assert _state(hass, entry.entry_id, key).state == EXPECTED[key][1]


@pytest.mark.parametrize("key", list(EXPECTED))
async def test_body_sensors_unknown_without_measurements(
    hass: HomeAssistant, setup_integration: SetupIntegration, key: str
) -> None:
    """A member without a scale measurement gets unknown states, not zeros."""
    entry = await setup_integration([])

    assert _state(hass, entry.entry_id, key).state == STATE_UNKNOWN
