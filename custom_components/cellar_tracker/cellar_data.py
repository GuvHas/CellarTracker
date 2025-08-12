"""Handles async data fetching and grouping from CellarTracker."""

import logging
import pandas as pd
from datetime import timedelta
import asyncio

from cellartracker import cellartracker

_LOGGER = logging.getLogger(__name__)


class WineCellarData:
    """Fetch and group data from CellarTracker asynchronously."""

    def __init__(self, hass, username: str, password: str, update_interval: timedelta):
        self._hass = hass
        self._username = username
        self._password = password
        self._update_interval = update_interval
        self._data = {}
        self._total_bottles = 0
        self._total_value = 0.0
        self._lock = asyncio.Lock()

    @property
    def total_bottles(self):
        return self._total_bottles

    @property
    def total_value(self):
        return self._total_value

    def get_readings(self):
        return self._data

    def get_reading(self, key: str):
        return self._data.get(key, {})

    async def async_update(self):
        """Fetch data from CellarTracker asynchronously and update internal state."""
        async with self._lock:
            _LOGGER.debug("Starting update from CellarTracker")

            def sync_fetch():
                client = cellartracker.CellarTracker(self._username, self._password)
                return client.get_inventory()

            try:
                inventory = await self._hass.async_add_executor_job(sync_fetch)
            except Exception as e:
                _LOGGER.error("Error fetching CellarTracker data: %s", e)
                return

            if not inventory:
                _LOGGER.warning("Empty inventory received from CellarTracker")
                return

            df = pd.DataFrame(inventory)
            _LOGGER.debug(f"Inventory columns: {df.columns.tolist()}")

            # Clean and convert numeric fields
            df['Valuation'] = (
                df['Valuation'].astype(str).str.replace(',', '.').astype(float)
            )
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

            # Compose wine key without size for sensor naming
            df['WineKey'] = df.apply(
                lambda x: f"{x['Vintage']} {x['Wine']}", axis=1
            )

            grouped = df.groupby('WineKey')
            total_valuation = df['Valuation'].sum()

            wine_data = {}
            total_bottles = 0
            total_value = 0.0

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
            _LOGGER.debug("CellarTracker data updated successfully")
