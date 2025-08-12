import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CellarTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CellarTracker."""

    VERSION = 1

    def __init__(self):
        self.data = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            username = user_input.get("username")
            password = user_input.get("password")

            # Simple validation could be here, e.g., test login
            # For now, just accept any input and proceed

            self.data = user_input

            return self.async_create_entry(title=username, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Optional("scan_interval", default=3600): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CellarTrackerOptionsFlowHandler(config_entry)

class CellarTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for CellarTracker."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "scan_interval",
                    default=self.config_entry.options.get("scan_interval", 3600),
                ): cv.positive_int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
