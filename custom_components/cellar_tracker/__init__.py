"""CellarTracker integration for Home Assistant using async."""

from datetime import timedelta
import logging

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .cellar_data import WineCellarData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the integration from yaml config (import)."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    username = conf["username"]
    password = conf["password"]
    scan_interval_seconds = max(conf.get("scan_interval", 3600), 30)
    scan_interval = timedelta(seconds=scan_interval_seconds)

    cellar_data = WineCellarData(hass, username, password, scan_interval)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["default"] = cellar_data

    # Trigger config entry for import
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=conf,
        )
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up cellar_tracker from a config entry."""
    username = entry.data.get("username")
    password = entry.data.get("password")
    scan_interval_seconds = max(entry.data.get("scan_interval", 3600), 30)
    scan_interval = timedelta(seconds=scan_interval_seconds)

    cellar_data = WineCellarData(hass, username, password, scan_interval)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = cellar_data

    # Forward setup of sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
