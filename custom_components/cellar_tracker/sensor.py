"""Platform for sensor integration."""
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from .cellar_data import WineCellarData
import logging
import re
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    if discovery_info is None:
        return

    devs = []
    cellar_data = hass.data[DOMAIN]
    master_data = cellar_data.get_readings()
    scan_interval = cellar_data.get_scan_interval()

    # Add wine grouped sensors
    for wine_key, data in master_data.items():
        devs.append(WineGroupedSensor("wine", wine_key, data, scan_interval))

    # Add total bottle and total value sensors
    devs.append(TotalBottleSensor(cellar_data, scan_interval))
    devs.append(TotalValueSensor(cellar_data, scan_interval))

    add_entities(devs, True)

class WineGroupedSensor(Entity):
    def __init__(self, sensor_type, wine_key, data, scan_interval):
        self._sensor_type = sensor_type
        self._wine_key = wine_key
        self._data = data
        self._state = data.get("wine", "unknown")
        self.update = Throttle(scan_interval)(self._update)

        name_without_size = re.sub(r'\s*\([^)]*\)\s*$', '', wine_key)
        self._slug = self._slugify(name_without_size)

    def _slugify(self, value):
        value = value.lower()
        value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
        return re.sub(r'[_]+', '-', value)

    @property
    def name(self):
        return f"cellar_tracker.{self._sensor_type}.{self._slug}"

    @property
    def unique_id(self):
        return f"cellar_tracker.{self._sensor_type}.{self._slug}"

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

    @property
    def unit_of_measurement(self):
        return None

    def _update(self):
        _LOGGER.debug(f"Updating sensor: {self.name}")
        self.hass.data[DOMAIN].update()
        master_data = self.hass.data[DOMAIN].get_readings()
        wine_info = master_data.get(self._wine_key, {})
        self._data = wine_info
        self._state = wine_info.get("wine", "unknown")

class TotalBottleSensor(Entity):
    def __init__(self, data_source, scan_interval):
        self._data_source = data_source
        self._state = 0
        self.update = Throttle(scan_interval)(self._update)

    @property
    def name(self):
        return "cellar_tracker.total_bottles"

    @property
    def unique_id(self):
        return "cellar_tracker.total_bottles"

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return "mdi:counter"

    @property
    def unit_of_measurement(self):
        return "bottles"

    def _update(self):
        _LOGGER.debug("Updating total bottles sensor")
        self._data_source.update()
        self._state = self._data_source.get_total_bottles()

class TotalValueSensor(Entity):
    def __init__(self, data_source, scan_interval):
        self._data_source = data_source
        self._state = 0.0
        self.update = Throttle(scan_interval)(self._update)

    @property
    def name(self):
        return "cellar_tracker.total_value"

    @property
    def unique_id(self):
        return "cellar_tracker.total_value"

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return "mdi:currency-eur"

    @property
    def unit_of_measurement(self):
        return "kr"  # or change to your currency

    def _update(self):
        _LOGGER.debug("Updating total value sensor")
        self._data_source.update()
        self._state = self._data_source.get_total_value()
