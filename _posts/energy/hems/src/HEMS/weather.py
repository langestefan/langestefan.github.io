"""
Weather data retrieval for the HEMS system.

Provides functions to fetch historical weather data from external APIs
(e.g. Open-Meteo) in a format ready for use with the Solar generation model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import requests


def fetch_open_meteo(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    timezone: str = "Europe/Amsterdam",
) -> pd.DataFrame:
    """Fetch historical hourly weather data from the Open-Meteo Archive API.

    Returns a DataFrame with columns needed by
    :meth:`Solar.compute_generation`: ``ghi``, ``dni``, ``dhi``,
    ``temp_air``, and ``wind_speed``.

    Args:
        latitude: Site latitude [degrees].
        longitude: Site longitude [degrees].
        start_date: Start date as ``"YYYY-MM-DD"`` (inclusive).
        end_date: End date as ``"YYYY-MM-DD"`` (inclusive).
        timezone: Timezone string for the returned timestamps
            (e.g. ``"Europe/Amsterdam"``).

    Returns:
        pd.DataFrame: Hourly weather data with a timezone-aware
        ``DatetimeIndex`` and columns:

        - **ghi** – Global horizontal irradiance [W/m²]
        - **dni** – Direct normal irradiance [W/m²]
        - **dhi** – Diffuse horizontal irradiance [W/m²]
        - **temp_air** – Air temperature at 2 m [°C]
        - **wind_speed** – Wind speed at 10 m [m/s]

    Raises:
        RuntimeError: If the API returns an error.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(
            [
                "shortwave_radiation",
                "direct_normal_irradiance",
                "diffuse_radiation",
                "temperature_2m",
                "wind_speed_10m",
            ]
        ),
        "timezone": timezone,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    if "error" in payload:
        raise RuntimeError(f"Open-Meteo API error: {payload['reason']}")

    hourly = payload["hourly"]

    idx = pd.DatetimeIndex(pd.to_datetime(hourly["time"]), name="time").tz_localize(
        timezone
    )

    df = pd.DataFrame(
        {
            "ghi": hourly["shortwave_radiation"],
            "dni": hourly["direct_normal_irradiance"],
            "dhi": hourly["diffuse_radiation"],
            "temp_air": hourly["temperature_2m"],
            "wind_speed": np.array(hourly["wind_speed_10m"]) / 3.6,  # km/h → m/s
        },
        index=idx,
    )

    # Replace any None values with 0 (can occur for recent/partial data)
    df = df.fillna(0.0)

    return df
