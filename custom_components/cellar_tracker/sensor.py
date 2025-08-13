# sensor.py

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .cellar_data import WineCellarData

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: WineCellarData = hass.data[DOMAIN][entry.entry_id]

    device_info = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "CellarTracker",
        "manufacturer": "CellarTracker",
        "model": "Online Cellar",
        "entry_type": "service",
    }

    sensors = [
        TotalBottlesSensor(coordinator, device_info, entry.entry_id),
        TotalValueSensor(coordinator, device_info, entry.entry_id),
    ]

    if coordinator.data and "bottles" in coordinator.data:
        for bottle_data in coordinator.data["bottles"]:
            if bottle_data.get("unique_bottle_id"):
                sensors.append(WineBottleSensor(coordinator, device_info, entry.entry_id, bottle_data))

    async_add_entities(sensors, update_before_add=True)


class TotalBottlesSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the total number of bottles in the cellar."""

    def __init__(self, coordinator, device_info, entry_id):
        super().__init__(coordinator)
        self._attr_name = "CellarTracker Total Bottles"
        self._attr_unique_id = f"{entry_id}_total_bottles"
        self._attr_icon = "mdi:bottle-wine"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("total_bottles", 0)


class TotalValueSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the total value of the cellar."""

    def __init__(self, coordinator, device_info, entry_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "CellarTracker Total Value"
        self._attr_unique_id = f"{entry_id}_total_value"
        self._attr_device_info = device_info

        # --- MODIFICATIONS START HERE ---

        # Set the icon to the Euro symbol
        self._attr_icon = "mdi:currency-eur"

        # Set the unit of measurement to "kr"
        self._attr_native_unit_of_measurement = "kr"
        
        # --- MODIFICATIONS END HERE ---

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("total_value", 0.0)


class WineBottleSensor(CoordinatorEntity, SensorEntity):
    """Represents a single bottle of wine in the cellar."""

    def __init__(self, coordinator, device_info, entry_id, bottle_data):
        """Initialize the wine bottle sensor."""
        super().__init__(coordinator)
        self.has_entity_name = True
        self._bottle_id = bottle_data["unique_bottle_id"]
        
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry_id}_{self._bottle_id}"
        
        wine_name = f"{bottle_data.get('Vintage', '')} {bottle_data.get('Wine', '')}".strip()
        self._attr_name = f"{wine_name} ({bottle_data.get('Bin') or 'No Bin'})"
        self._attr_icon = "mdi:bottle-wine"

    @property
    def _current_bottle_data(self) -> dict | None:
        """Find the data for this specific bottle from the coordinator's latest update."""
        return next(
            (bottle for bottle in self.coordinator.data.get("bottles", []) 
             if bottle.get("unique_bottle_id") == self._bottle_id),
            None
        )

    @property
    def available(self) -> bool:
        """Return True if the bottle exists in the coordinator's data and the coordinator is available."""
        return self.coordinator.last_update_success and self._current_bottle_data is not None

    @property
    def native_value(self):
        """Return the state of the sensor (the bottle's location)."""
        if data := self._current_bottle_data:
            return data.get("Location")
        return None

    @property
    def extra_state_attributes(self):
        """Return all other details of the bottle as attributes."""
        if data := self._current_bottle_data:
            return data
        return {}