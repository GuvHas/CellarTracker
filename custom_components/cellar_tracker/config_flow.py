"""Config flow for CellarTracker integration."""
import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .cellar_data import WineCellarData
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 3600

class CellarTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            scan_interval_seconds = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            scan_interval = timedelta(seconds=max(scan_interval_seconds, 30))

            # Try to validate credentials by fetching inventory once
            cellar_data = WineCellarData(self.hass, username, password, scan_interval)
            try:
                await cellar_data.async_update()
            except Exception as e:
                _LOGGER.error("Failed to fetch CellarTracker data: %s", e)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"CellarTracker ({username})",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        "scan_interval": scan_interval_seconds,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
