"""Sensor platform for CellarTracker integration."""

import logging
import re
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .cellar_data import WineCellarData
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for CellarTracker from a config entry."""
    cellar_data: WineCellarData = hass.data[DOMAIN][entry.entry_id]

    await cellar_data.async_update()

    sensors = []

    # Create wine sensors
    for wine_key, data in cellar_data.get_readings().items():
        sensors.append(WineGroupedSensor(entry.entry_id, wine_key, data, cellar_data))

    # Total bottles and total value sensors
    sensors.append(TotalBottleSensor(entry.entry_id, cellar_data))
    sensors.append(TotalValueSensor(entry.entry_id, cellar_data))

    async_add_entities(sensors, True)

class WineGroupedSensor(Entity):
    def __init__(self, entry_id, wine_key, data, cellar_data: WineCellarData):
        self._entry_id = entry_id
        self._wine_key = wine_key
        self._data = data
        self._cellar_data = cellar_data
        self._state = data.get("wine", "unknown")

        # Slugify for unique_id and entity_id
        name_without_size = re.sub(r'\s*\([^)]*\)\s*$', '', wine_key)
        slug = self._slugify(name_without_size)
        self._unique_id = f"cellar_tracker.wine.{slug}"

    def _slugify(self, value):
        value = value.lower()
        value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
        return re.sub(r'[_]+', '-', value)

    @property
    def name(self):
        return f"CellarTracker: {self._data.get('wine', 'unknown')}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        attrs = self._data.copy()
        attrs.pop("wine", None)
        return attrs

    @property
    def icon(self):
        return "mdi:bottle-wine"

    async def async_update(self):
        await self._cellar_data.async_update()
        master_data = self._cellar_data.get_readings()
        wine_info = master_data.get(self._wine_key, {})
        self._data = wine_info
        self._state = wine_info.get("wine", "unknown")

class TotalBottleSensor(Entity):
    def __init__(self, entry_id, cellar_data: WineCellarData):
        self._entry_id = entry_id
        self._cellar_data = cellar_data
        self._state = None

    @property
    def name(self):
        return "CellarTracker Total Bottles"

    @property
    def unique_id(self):
        return f"cellar_tracker_total_bottles_{self._entry_id}"

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return "mdi:counter"

    @property
    def unit_of_measurement(self):
        return "bottles"

    async def async_update(self):
        await self._cellar_data.async_update()
        self._state = self._cellar_data.get_total_bottles()

class TotalValueSensor(Entity):
    def __init__(self, entry_id, cellar_data: WineCellarData):
        self._entry_id = entry_id
        self._cellar_data = cellar_data
        self._state = None

    @property
    def name(self):
        return "CellarTracker Total Value"

    @property
    def unique_id(self):
        return f"cellar_tracker_total_value_{self._entry_id}"

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return "mdi:currency-eur"

    @property
    def unit_of_measurement(self):
        return "kr"

    async def async_update(self):
        await self._cellar_data.async_update()
        self._state = self._cellar_data.get_total_value()
