"""
Solar generation modeling and prototyping for HEMS.

This includes:
- A solar generation model backed by pvlib (PVWatts approach).
- The solar generation is treated as a negative load (i.e. power injection) in the HEMS
  framework.
- The generation profile can include controllable curtailment so the optimiser can
  spill excess solar when beneficial.
"""

from __future__ import annotations

import cvxpy as cp
import numpy as np
import pandas as pd
import pvlib
from HEMS.base import GenericLoad
from pvlib.location import Location


class Solar(GenericLoad):
    """A solar PV generation model for the HEMS system.

    Uses the PVWatts DC model and PVWatts inverter model from *pvlib* to
    convert plane-of-array irradiance and cell temperature into AC power.
    An optional curtailment variable allows the optimiser to reduce injection
    when that is beneficial (e.g. to avoid feed-in limits).

    The net power ``P`` is a CVXPY variable (when curtailable) or parameter
    (when fixed), representing the AC power injected by the PV system in kW.
    Positive values mean power flowing *into* the home / grid.
    """

    def __init__(
        self,
        T: int,
        dt: float = 0.25,
        name: str = "Solar",
        # --- array physical parameters ---
        surface_tilt: float = 35.0,
        surface_azimuth: float = 180.0,
        latitude: float = 52.0,
        longitude: float = 5.0,
        altitude: float = 0.0,
        timezone: str = "Europe/Amsterdam",
        # --- sizing ---
        pdc0: float = 5.0,
        pac0: float | None = None,
        # --- PVWatts model parameters ---
        gamma_pdc: float = -0.004,
        eta_inv: float = 0.96,
        # --- curtailment ---
        curtailable: bool = False,
    ):
        """Initialize the solar generation model.

        Args:
            T: Time horizon (number of time steps).
            dt: Duration of each time step in hours (default 0.25 = 15 min).
            name: Name identifier for the solar source.
            surface_tilt: Tilt angle of the PV modules from horizontal [degrees].
            surface_azimuth: Azimuth angle of the PV modules.
                180° = south-facing (Northern Hemisphere default) [degrees].
            latitude: Site latitude [degrees].
            longitude: Site longitude [degrees].
            altitude: Site altitude above sea level [m].
            timezone: Timezone string for the site (e.g. ``"Europe/Amsterdam"``).
            pdc0: Nameplate DC rating of the array at STC [kW].
            pac0: AC power limit (inverter size) [kW].
                Defaults to ``pdc0`` if not provided.
            gamma_pdc: Temperature coefficient of power [1/°C].
                Typical range: -0.002 to -0.005.
            eta_inv: Nominal inverter efficiency (used by PVWatts inverter model).
            curtailable: If ``True``, ``P`` is a CVXPY variable
                that can be curtailed via :meth:`constraints`.
                If ``False``, ``P`` is a fixed parameter.
        """
        super().__init__(name, T)
        self.dt = dt

        # --- Array & location ---
        self.surface_tilt = surface_tilt
        self.surface_azimuth = surface_azimuth
        self.location = Location(
            latitude, longitude, tz=timezone, altitude=altitude, name=name
        )

        # --- Sizing (stored in kW, pvlib uses W internally) ---
        self.pdc0 = pdc0
        self.pac0 = pac0 if pac0 is not None else pdc0
        self.gamma_pdc = gamma_pdc
        self.eta_inv = eta_inv

        # --- Curtailment mode ---
        self.curtailable = curtailable

        # Maximum available AC power computed by pvlib [kW] — always a parameter
        self.P_max = cp.Parameter(T, nonneg=True, name=f"{name}_Pmax_kW")
        self.P_max.value = np.zeros(T)

        if curtailable:
            # P is a decision variable the optimiser can curtail
            self.P = cp.Variable(T, nonneg=True, name=f"{name}_P_kW")
        else:
            # P is fixed to whatever pvlib computes
            self.P = cp.Parameter(T, nonneg=True, name=f"{name}_P_kW")
            self.P.value = np.zeros(T)

    # ------------------------------------------------------------------
    # pvlib computation
    # ------------------------------------------------------------------

    def compute_generation(
        self,
        times: pd.DatetimeIndex,
        ghi: np.ndarray,
        temp_air: np.ndarray,
        wind_speed: np.ndarray | None = None,
        dni: np.ndarray | None = None,
        dhi: np.ndarray | None = None,
    ) -> np.ndarray:
        """Compute AC power output using pvlib and store it in ``P_max``.

        Uses the Erbs model to decompose GHI into DNI/DHI (if not provided),
        transposes irradiance onto the tilted plane, estimates cell temperature,
        then applies the PVWatts DC + inverter models.

        Args:
            times: DatetimeIndex aligned with the time steps (length ``T``).
            ghi: Global horizontal irradiance [W/m²], shape ``(T,)``.
            temp_air: Ambient air temperature [°C], shape ``(T,)``.
            wind_speed: Wind speed at measurement height [m/s], shape ``(T,)``.
                Defaults to 1 m/s everywhere if not supplied.
            dni: Direct normal irradiance [W/m²], shape ``(T,)``.
                If ``None``, estimated from ``ghi`` using the Erbs model.
            dhi: Diffuse horizontal irradiance [W/m²], shape ``(T,)``.
                If ``None``, estimated from ``ghi`` using the Erbs model.

        Returns:
            AC power output in kW, shape ``(T,)``.
        """
        if len(times) != self.T:
            raise ValueError(f"len(times)={len(times)} does not match T={self.T}")

        ghi = np.asarray(ghi, dtype=float)
        temp_air = np.asarray(temp_air, dtype=float)
        if wind_speed is None:
            wind_speed = np.ones(self.T)
        else:
            wind_speed = np.asarray(wind_speed, dtype=float)

        # --- Solar position ---
        solpos = self.location.get_solarposition(times)
        solar_zenith = np.asarray(solpos["apparent_zenith"])
        solar_azimuth = np.asarray(solpos["azimuth"])

        # --- DNI / DHI decomposition (Erbs) if not provided ---
        if dni is None or dhi is None:
            dni_extra = np.asarray(pvlib.irradiance.get_extra_radiation(times))
            erbs = pvlib.irradiance.erbs_driesse(ghi, solar_zenith, dni_extra=dni_extra)
            if dni is None:
                dni = np.asarray(erbs["dni"], dtype=float)
            if dhi is None:
                dhi = np.asarray(erbs["dhi"], dtype=float)
        dni = np.asarray(dni, dtype=float)
        dhi = np.asarray(dhi, dtype=float)

        # --- Plane-of-array irradiance ---
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.surface_tilt,
            surface_azimuth=self.surface_azimuth,
            solar_zenith=solar_zenith,
            solar_azimuth=solar_azimuth,
            dni=dni,
            ghi=ghi,
            dhi=dhi,
        )
        poa_global = np.maximum(np.asarray(poa["poa_global"]), 0.0)

        # --- Cell temperature (SAPM open-rack glass/glass) ---
        temp_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"][
            "open_rack_glass_glass"
        ]
        temp_cell = pvlib.temperature.sapm_cell(
            poa_global, temp_air, wind_speed, **temp_params
        )

        # --- DC power (PVWatts), pdc0 in W ---
        pdc = pvlib.pvsystem.pvwatts_dc(
            effective_irradiance=poa_global,
            temp_cell=temp_cell,
            pdc0=self.pdc0 * 1000.0,
            gamma_pdc=self.gamma_pdc,
        )
        pdc = np.maximum(pdc, 0.0)

        # --- AC power (PVWatts inverter), pac0 in W ---
        pac = pvlib.inverter.pvwatts(
            pdc=pdc,
            pdc0=self.pac0 * 1000.0 / self.eta_inv,
            eta_inv_nom=self.eta_inv,
        )
        pac_kw = np.maximum(pac / 1000.0, 0.0)  # Convert W → kW

        # --- Store in parameters ---
        self.P_max.value = pac_kw

        if not self.curtailable:
            self.P.value = pac_kw  # type: ignore[union-attr]

        return pac_kw

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    def constraints(self) -> list:
        """Return CVXPY constraints for the solar generator.

        When ``curtailable=True``:
            - ``0 <= P[t] <= P_max[t]``  (optimiser can reduce injection)

        When ``curtailable=False`` an empty list is returned because ``P``
        is a fixed parameter.

        Returns:
            list: CVXPY constraints.
        """
        if not self.curtailable:
            return []

        return [self.P <= self.P_max]
