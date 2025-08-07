"""CellarTracker integration for Home Assistant."""

from .cellar_data import WineCellarData
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.helpers import discovery as hdisco
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging

DOMAIN = "cellar_tracker"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=3600): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass, config):
    conf = config[DOMAIN]

    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]
    scan_interval_seconds = max(conf[CONF_SCAN_INTERVAL], 30)  # Min 30 sek
    scan_interval = timedelta(seconds=scan_interval_seconds)

    _LOGGER.debug("Initializing CellarTracker with scan interval %s", scan_interval)

    hass.data[DOMAIN] = WineCellarData(username, password, scan_interval)
    hass.data[DOMAIN].update()

    hdisco.load_platform(hass, "sensor", DOMAIN, {}, config)

    return True
