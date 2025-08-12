"""Sensor platform for CellarTracker integration."""

import logging
import re
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType

from .cellar_data import WineCellarData
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType = None,
) -> None:
    """Set up the sensor platform for CellarTracker."""
    cellar_data: WineCellarData = hass.data[DOMAIN][entry.entry_id]

    await cellar_data.async_update()

    sensors = []

    # Add total bottles sensor
    sensors.append(CellarTotalBottlesSensor(cellar_data))
    # Add total value sensor
    sensors.append(CellarTotalValueSensor(cellar_data))

    # Add per-wine sensors
    for wine_key, data in cellar_data.get_readings().items():
        sensors.append(WineGroupedSensor(wine_key, data, cellar_data))

    async_add_entities(sensors, True)


class CellarTotalBottlesSensor(Entity):
    def __init__(self, cellar_data: WineCellarData):
        self._cellar_data = cellar_data
        self._state = None

    @property
    def name(self) -> str:
        return "cellar_tracker.total_bottles"

    @property
    def unique_id(self) -> str:
        return "cellar_tracker_total_bottles"

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:glass-wine"

    async def async_update(self):
        await self._cellar_data.async_update()
        self._state = self._cellar_data.total_bottles


class CellarTotalValueSensor(Entity):
    def __init__(self, cellar_data: WineCellarData):
        self._cellar_data = cellar_data
        self._state = None

    @property
    def name(self) -> str:
        return "cellar_tracker.total_value"

    @property
    def unique_id(self) -> str:
        return "cellar_tracker_total_value"

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:currency-eur"

    @property
    def unit_of_measurement(self):
        return "kr"

    async def async_update(self):
        await self._cellar_data.async_update()
        self._state = self._cellar_data.total_value


class WineGroupedSensor(Entity):
    def __init__(self, wine_key: str, data: dict, cellar_data: WineCellarData):
        self._wine_key = wine_key
        self._data = data
        self._cellar_data = cellar_data
        self._state = data.get("wine", "unknown")

        # Create slug removing size info from wine_key, e.g. "2011 Some Wine (750ml)" -> "2011-some-wine"
        name_without_size = re.sub(r"\s*\([^)]*\)\s*$", "", wine_key)
        self._slug = self._slugify(name_without_size)

    def _slugify(self, value: str) -> str:
        value = value.lower()
        value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
        return re.sub(r"[-]+", "-", value)

    @property
    def name(self) -> str:
        return f"cellar_tracker.wine.{self._slug}"

    @property
    def unique_id(self) -> str:
        return f"cellar_tracker.wine.{self._slug}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        attrs = self._data.copy()
        attrs.pop("wine", None)
        return attrs

    @property
    def icon(self) -> str:
        return "mdi:bottle-wine"

    @property
    def unit_of_measurement(self):
        return None

    async def async_update(self):
        _LOGGER.debug(f"Updating sensor {self.name}")
        await self._cellar_data.async_update()
        updated_data = self._cellar_data.get_reading(self._wine_key)
        self._data = updated_data
        self._state = updated_data.get("wine", "unknown")
