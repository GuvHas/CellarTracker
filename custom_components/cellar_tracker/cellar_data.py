import logging
import asyncio
import async_timeout
import pandas as pd
from datetime import timedelta
from cellartracker import cellartracker

_LOGGER = logging.getLogger(__name__)

class WineCellarData:
    """Async data handler for CellarTracker."""

    def __init__(self, hass, username, password, update_interval: timedelta):
        self.hass = hass
        self.username = username
        self.password = password
        self.update_interval = update_interval
        self._data = {}
        self._total_bottles = 0
        self._total_value = 0.0
        self._last_update = None
        self._lock = asyncio.Lock()

    async def async_update(self):
        """Fetch data asynchronously, throttle by update_interval."""
        async with self._lock:
            # Throttle: if last update was recent, skip
            if self._last_update:
                elapsed = self.hass.loop.time() - self._last_update
                if elapsed < self.update_interval.total_seconds():
                    return

            _LOGGER.debug("Updating wine data from CellarTracker")

            try:
                async with async_timeout.timeout(15):
                    # Run sync IO in executor to avoid blocking event loop
                    inventory = await self.hass.async_add_executor_job(
                        self._fetch_inventory
                    )
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout fetching data from CellarTracker")
                return
            except Exception as e:
                _LOGGER.error("Error fetching data from CellarTracker: %s", e)
                return

            if not inventory:
                _LOGGER.warning("No inventory data received from CellarTracker")
                return

            df = pd.DataFrame(inventory)
            _LOGGER.debug(f"Inventory columns: {df.columns.tolist()}")

            # Clean data, convert Valuation to float (comma to dot)
            df['Valuation'] = df['Valuation'].astype(str).str.replace(',', '.').astype(float)
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

            # Create a unique wine key including vintage but NOT size (since size is stripped later)
            df['WineKey'] = df.apply(lambda x: f"{x['Vintage']} {x['Wine']}", axis=1)

            total_valuation = df['Valuation'].sum()

            wine_data = {}
            total_bottles = 0
            total_value = 0.0

            grouped = df.groupby('WineKey')

            for key, group in grouped:
                count = len(group)
                value_total = float(group['Valuation'].sum())
                value_avg = float(group['Valuation'].mean())
                percentage = (value_total / total_valuation * 100) if total_valuation > 0 else 0.0

                total_bottles += count
                total_value += value_total

                first = group.iloc[0]

                wine_data[key] = {
                    "count": count,
                    "value_total": value_total,
                    "value_avg": value_avg,
                    "%": percentage,
                    "vintage": first["Vintage"],
                    "wine": first["Wine"],
                    "varietal": first.get("Varietal", ""),
                    "producer": first.get("Producer", ""),
                    "type": first.get("Type", ""),
                    "appellation": first.get("Appellation", ""),
                    "country": first.get("Country", ""),
                    "region": first.get("Region", ""),
                    "location": first.get("Location", ""),
                    "store": first.get("StoreName", ""),
                    "size": first["Size"],
                    "beginconsume": first["BeginConsume"],
                    "endconsume": first["EndConsume"],
                    "bins": [b for b in group["Bin"] if b],
                }

            self._data = wine_data
            self._total_bottles = total_bottles
            self._total_value = round(total_value, 2)
            self._last_update = self.hass.loop.time()

    def _fetch_inventory(self):
        """Sync fetch inventory from cellartracker package."""
        client = cellartracker.CellarTracker(self.username, self.password)
        inventory = client.get_inventory()
        return inventory

    def get_wine_keys(self):
        return list(self._data.keys())

    def get_wine_info(self, key):
        return self._data.get(key)

    def get_total_bottles(self):
        return self._total_bottles

    def get_total_value(self):
        return self._total_value
