# cellar_data.py

import logging
from datetime import timedelta
import hashlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class WineCellarData(DataUpdateCoordinator):
    """Fetch and process CellarTracker inventory data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the data coordinator."""
        self._hass = hass
        self._username = entry.data["username"]
        self._password = entry.data["password"]

        scan_interval = timedelta(
            seconds=entry.options.get("scan_interval", entry.data.get("scan_interval", 3600))
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        
        from cellartracker import cellartracker
        self._client = cellartracker.CellarTracker(self._username, self._password)


    def _process_inventory(self, inventory: list) -> dict:
        """Process the raw inventory list into a structured dictionary."""
        if not inventory:
            _LOGGER.warning("CellarTracker returned empty inventory")
            return {"total_bottles": 0, "total_value": 0.0, "bottles": []}

        total_value = 0.0
        processed_bottles = []
        
        # Keep track of generated IDs to ensure they are truly unique.
        seen_ids = set()

        for bottle in inventory:
            if 'iWine' not in bottle:
                _LOGGER.warning("Skipping bottle because it's missing the 'iWine' identifier: %s", bottle)
                continue

            # --- STABLE UNIQUE ID GENERATION ---
            # Create a stable ID from attributes that don't change.
            # We combine multiple attributes to ensure uniqueness.
            # Using a hash prevents the ID from becoming excessively long.
            
            base_id_string = (
                f"{bottle['iWine']}_"
                f"{bottle.get('PurchaseDate', '')}_"
                f"{bottle.get('Barcode', '')}_"
                f"{bottle.get('Location', '')}_"
                f"{bottle.get('Bin', '')}"
            )
            
            # If multiple bottles have the exact same attributes, we add a counter.
            counter = 0
            unique_id = hashlib.sha1(base_id_string.encode('utf-8')).hexdigest()[:16]
            temp_id = unique_id
            
            while temp_id in seen_ids:
                counter += 1
                temp_id = f"{unique_id}_{counter}"
            
            unique_id = temp_id
            seen_ids.add(unique_id)
            bottle['unique_bottle_id'] = unique_id
            # --- END OF STABLE ID LOGIC ---

            try:
                valuation = float(bottle.get('Valuation', 0.0))
                bottle['Valuation'] = valuation
                total_value += valuation
            except (ValueError, TypeError):
                bottle['Valuation'] = 0.0
            
            processed_bottles.append(bottle)
        
        total_bottles = len(processed_bottles)

        return {
            "total_bottles": total_bottles,
            "total_value": round(total_value, 2),
            "bottles": processed_bottles,
        }

    async def _async_update_data(self) -> dict:
        """Fetch inventory from CellarTracker asynchronously."""
        try:
            inventory_list = await self._hass.async_add_executor_job(self._client.get_inventory)
            return await self._hass.async_add_executor_job(self._process_inventory, inventory_list)

        except Exception as e:
            _LOGGER.error("Error communicating with CellarTracker API: %s", e)
            raise UpdateFailed(f"Error communicating with CellarTracker API: {e}")