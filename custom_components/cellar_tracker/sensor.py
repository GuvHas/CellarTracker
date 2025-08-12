import logging
import re
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .cellar_data import WineCellarData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors based on config entry."""
    cellar_data: WineCellarData = hass.data[DOMAIN][entry.entry_id]

    await cellar_data.async_update()  # Fetch initial data

    devs = []

    # Add wine sensors for each wine key
    for wine_key in cellar_data.get_wine_keys():
        devs.append(CellarWineSensor(cellar_data, wine_key))

    # Add total bottles and total value sensors
    devs.append(TotalBottleSensor(cellar_data))
    devs.append(TotalValueSensor(cellar_data))

    async_add_entities(devs, update_before_add=True)


class CellarWineSensor(Entity):
    """Representation of a wine sensor."""

    def __init__(self, cellar_data: WineCellarData, wine_key: str):
        self.cellar_data = cellar_data
        self.wine_key = wine_key

        # Remove size info from wine_key for sensor name/id
        clean_name = self._remove_size_from_name(wine_key)

        self._attr_name = f"cellar_tracker_wine_{self._slugify(clean_name)}"
        self._attr_unique_id = self._attr_name

        self._state = None
        self._attributes = {}

    def _remove_size_from_name(self, name: str) -> str:
        # Remove patterns like '750ml', '1.5L', '500 ml' etc.
        return re.sub(r'\b\d+(\.\d+)?\s?(ml|l|cl)\b', '', name, flags=re.IGNORECASE).strip()

    def _slugify(self, value: str) -> str:
        value = value.lower()
        value = re.sub(r'[^a-z0-9]+', '_', value).strip('_')
        return value

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        """Fetch updated state from coordinator."""
        await self.cellar_data.async_update()
        wine_info = self.cellar_data.get_wine_info(self.wine_key)

        if wine_info:
            self._state = wine_info.get("count", 0)
            # Copy all other info except count to attributes
            self._attributes = {k: v for k, v in wine_info.items() if k != "count"}
        else:
            self._state = None
            self._attributes = {}


class TotalBottleSensor(Entity):
    """Sensor for total bottles in cellar."""

    def __init__(self, cellar_data: WineCellarData):
        self.cellar_data = cellar_data
        self._attr_name = "cellar_tracker_total_bottles"
        self._attr_unique_id = self._attr_name
        self._state = None

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

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
        await self.cellar_data.async_update()
        self._state = self.cellar_data.get_total_bottles()


class TotalValueSensor(Entity):
    """Sensor for total cellar value."""

    def __init__(self, cellar_data: WineCellarData):
        self.cellar_data = cellar_data
        self._attr_name = "cellar_tracker_total_value"
        self._attr_unique_id = self._attr_name
        self._state = None

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

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
        await self.cellar_data.async_update()
        self._state = self.cellar_data.get_total_value()
