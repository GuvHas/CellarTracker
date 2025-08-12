"""Handles data fetching and grouping from CellarTracker asynchronously."""

import logging
from datetime import timedelta
import asyncio

import pandas as pd
from homeassistant.util import Throttle

from cellartracker import cellartracker  # Ensure cellartracker is installed and async-capable or wrap sync

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=3600)

class WineCellarData:
    """Fetch and group data from CellarTracker."""

    def __init__(self, hass, username, password, scan_interval: timedelta):
        self._hass = hass
        self._username = username
        self._password = password
        self._scan_interval = scan_interval
        self._data = {}
        self._total_bottles = 0
        self._total_value = 0.0

        # Throttle updates
        self.async_update = Throttle(scan_interval)(self._async_update)

    def get_readings(self):
        return self._data

    def get_total_bottles(self):
        return self._total_bottles

    def get_total_value(self):
        return self._total_value

    async def _async_update(self, **kwargs):
        """Fetch inventory data asynchronously."""
        _LOGGER.debug("Updating data from CellarTracker")

        # Since cellartracker library is likely sync, run in executor
        def fetch_inventory():
            client = cellartracker.CellarTracker(self._username, self._password)
            return client.get_inventory()

        try:
            inventory = await self._hass.async_add_executor_job(fetch_inventory)
        except Exception as err:
            _LOGGER.error("Error fetching CellarTracker inventory: %s", err)
            return

        if not inventory:
            _LOGGER.warning("Empty inventory received")
            return

        df = pd.DataFrame(inventory)
        _LOGGER.debug(f"Columns in inventory: {df.columns.tolist()}")

        # Clean and convert data
        df['Valuation'] = df['Valuation'].astype(str).str.replace(',', '.').astype(float)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['WineKey'] = df.apply(lambda x: f"{x['Vintage']} {x['Wine']} ({x['Size']})", axis=1)

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
