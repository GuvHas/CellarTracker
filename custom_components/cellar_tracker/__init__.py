"""The CellarTracker integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .cellar_data import WineCellarData
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CellarTracker from a config entry."""
    # Create the coordinator
    coordinator = WineCellarData(hass, entry)
    
    # Perform the first refresh to fetch data before setting up platforms
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add a listener to handle options updates
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove coordinator from hass.data if unload was successful
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # This will automatically trigger a reload of the integration
    await hass.config_entries.async_reload(entry.entry_id)