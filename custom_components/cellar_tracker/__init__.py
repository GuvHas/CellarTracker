"""CellarTracker integration for Home Assistant using async."""

from datetime import timedelta
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .cellar_data import WineCellarData

DOMAIN = "cellar_tracker"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("username"): cv.string,
                vol.Required("password"): cv.string,
                vol.Optional("scan_interval", default=3600): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the cellar_tracker component from YAML config."""
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

    # Import YAML config as a config entry
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

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload cellar_tracker config entry and remove its entities."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        # Remove all entities linked to this config entry from entity registry
        entity_registry = er.async_get(hass)
        to_remove = [
            entity_id
            for entity_id, entity in entity_registry.entities.items()
            if entity.config_entry_id == entry.entry_id
        ]
        for entity_id in to_remove:
            entity_registry.async_remove(entity_id)

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
