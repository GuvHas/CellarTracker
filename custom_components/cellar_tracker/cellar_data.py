"""Handles data fetching and grouping from CellarTracker."""

import logging
import pandas as pd
from cellartracker import cellartracker
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

class WineCellarData:
    """Fetch and group data from CellarTracker."""

    def __init__(self, username, password, scan_interval):
        self._username = username
        self._password = password
        self._scan_interval = scan_interval
        self.update = Throttle(scan_interval)(self._update)
        self._data = {}
        self._total_bottles = 0
        self._total_value = 0.0

    def get_readings(self):
        return self._data

    def get_reading(self, key):
        return self._data.get(key, {})

    def get_scan_interval(self):
        return self._scan_interval

    def get_total_bottles(self):
        return self._total_bottles

    def get_total_value(self):
        return self._total_value

    def _update(self, **kwargs):
        _LOGGER.debug("Updating data from CellarTracker")

        client = cellartracker.CellarTracker(self._username, self._password)
        inventory = client.get_inventory()

        if not inventory:
            _LOGGER.warning("Empty inventory received")
            return

        df = pd.DataFrame(inventory)
        _LOGGER.debug(f"Columns in inventory: {df.columns.tolist()}")

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