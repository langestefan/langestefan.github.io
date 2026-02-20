"""
Heat pump model for the HEMS system.

Models an air-source heat pump as a **fixed** (non-controllable) load.
The electricity consumption is derived from a 1R1C building thermal model
and a temperature-dependent Coefficient of Performance (COP).

1R1C model
----------

.. math::

    C \\frac{dT_\\text{in}}{dt}
        = \\frac{T_\\text{amb} - T_\\text{in}}{R}
          + Q_\text{hp} + Q_\text{int}

where

- :math:`C` is the lumped thermal capacity of the building [kWh/°C],
- :math:`R = 1/H` is the thermal resistance [°C/kW],
- :math:`H` is the total heat-loss coefficient [kW/°C],
- :math:`Q_\\text{hp}` is the thermal power delivered by the heat pump [kW],- :math:`Q_\text{int}` is the internal heat gain (occupants, appliances, lighting) [kW],- :math:`T_\\text{in}` is the indoor (node) temperature [°C],
- :math:`T_\\text{amb}` is the outdoor ambient temperature [°C].

At every time step the heat pump delivers exactly the thermal power needed
to maintain the indoor set-point temperature.  The electrical power is then
:math:`P_\\text{el} = Q_\\text{hp} / \\text{COP}(T_\\text{amb}, T_\\text{supply})`.
"""

from __future__ import annotations

import numpy as np

from .base import FixedLoad
from .const import DT_DEFAULT


class HeatPump(FixedLoad):
    """An air-source heat pump modelled as a non-controllable fixed load.

    The model couples a simple 1R1C building envelope with a COP curve to
    produce a time-varying electrical power profile that keeps the indoor
    temperature at the desired set-point.

    The COP is modelled as ideal Carnot efficiency scaled by a constant
    second-law efficiency :math:`\\eta_{\\text{Carnot}}`:

    .. math::

        \\text{COP} = \\eta_{\\text{Carnot}} \\cdot
                      \\frac{T_{\\text{supply}}}{T_{\\text{supply}} - T_{\\text{amb}}}

    clamped to ``[cop_min, cop_max]``.
    """

    def __init__(
        self,
        T_amb: np.ndarray,
        dt: float = DT_DEFAULT,
        name: str = "HeatPump",
        # --- building envelope (1R1C) ---
        H: float = 0.20,
        C: float = 8.0,
        T_set: float = 20.0,
        T_in_0: float = 20.0,
        # --- heat-pump parameters ---
        T_supply: float = 35.0,
        eta_carnot: float = 0.45,
        cop_min: float = 1.5,
        cop_max: float = 6.0,
        P_hp_max: float = 8.0,
        # --- internal gains ---
        Q_int: float = 0.7,
    ):
        """Initialise the heat-pump model.

        The constructor immediately runs the 1R1C simulation for *T*
        time steps and stores the resulting electrical power profile in
        ``self.P`` (a CVXPY parameter).

        Args:
            T_amb: Outdoor ambient temperature [°C], shape ``(T,)``.
                The number of time steps is inferred from this array.
            dt: Duration of each time step [h].
            name: Name identifier.
            H: Total heat-loss coefficient of the building [kW/°C].
            C: Lumped thermal capacity of the building [kWh/°C].
            T_set: Indoor temperature set-point [°C].
            T_in_0: Initial indoor temperature [°C].
            T_supply: Heat-pump supply (condenser outlet) temperature [°C].
            eta_carnot: Second-law (Carnot) efficiency of the heat pump [-].
            cop_min: Minimum allowed COP (clamp) [-].
            cop_max: Maximum allowed COP (clamp) [-].
            P_hp_max: Maximum thermal output of the heat pump [kW].
            Q_int: Internal heat gain from occupants, appliances and
                lighting [kW].  Typical range 0.5–1.0 kW for a
                Dutch dwelling.
        """
        T_amb = np.asarray(T_amb, dtype=float)
        T = len(T_amb)

        # Store building & HP parameters for later inspection
        self.dt = dt
        self.H = H
        self.C = C
        self.T_set = T_set
        self.T_supply = T_supply
        self.eta_carnot = eta_carnot
        self.cop_min = cop_min
        self.cop_max = cop_max
        self.P_hp_max = P_hp_max
        self.Q_int = Q_int

        # --- Run 1R1C simulation ---
        Q_hp, T_in, cop = self._simulate(T_amb, T_in_0)

        # Store trajectories for plotting / inspection
        self.T_amb = T_amb
        self.T_in = T_in  # length T+1
        self.Q_hp = Q_hp  # thermal power [kW], length T
        self.cop = cop  # COP at each step, length T

        # Electrical power profile [kW]
        P_el = np.where(cop > 0, Q_hp / cop, 0.0)

        # Initialise FixedLoad with the computed electrical profile
        super().__init__(name, P_el)

    # ------------------------------------------------------------------
    # COP model
    # ------------------------------------------------------------------

    def compute_cop(self, T_amb: np.ndarray) -> np.ndarray:
        """Compute the COP for given ambient temperatures.

        Uses a Carnot-based COP model clamped to ``[cop_min, cop_max]``.

        Args:
            T_amb: Ambient (source-side) temperature [°C].

        Returns:
            COP array, same shape as *T_amb*.
        """
        T_amb = np.asarray(T_amb, dtype=float)

        # Kelvin
        T_h = self.T_supply + 273.15
        T_c = T_amb + 273.15

        # Avoid division by zero when T_supply ≈ T_amb
        dT = np.maximum(T_h - T_c, 1.0)

        cop_carnot = T_h / dT
        cop = self.eta_carnot * cop_carnot

        return np.clip(cop, self.cop_min, self.cop_max)

    # ------------------------------------------------------------------
    # 1R1C thermal simulation
    # ------------------------------------------------------------------

    def _simulate(
        self,
        T_amb: np.ndarray,
        T_in_0: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run a forward Euler 1R1C simulation.

        At each step the controller injects the thermal power
        required to bring the indoor temperature back to the set-point,
        clamped between 0 (no cooling mode) and ``P_hp_max``.

        Args:
            T_amb: Ambient temperature [°C], shape ``(T,)``.
            T_in_0: Initial indoor temperature [°C].

        Returns:
            Tuple ``(Q_hp, T_in, cop)`` where

            - **Q_hp** – thermal power [kW], shape ``(T,)``
            - **T_in** – indoor temperature [°C], shape ``(T+1,)``
            - **cop** – COP at each step, shape ``(T,)``
        """
        T = len(T_amb)

        T_in = np.zeros(T + 1)
        Q_hp = np.zeros(T)
        T_in[0] = T_in_0

        cop = self.compute_cop(T_amb)

        for t in range(T):
            # Heat loss this step (positive = heat leaves the building)
            Q_loss = self.H * (T_in[t] - T_amb[t])

            # Net thermal power the HP must supply after internal gains:
            #   C * (T_set - T_in[t]) / dt = Q_hp + Q_int - Q_loss
            #   => Q_hp = C * (T_set - T_in[t]) / dt + Q_loss - Q_int
            Q_needed = self.C * (self.T_set - T_in[t]) / self.dt + Q_loss - self.Q_int

            # Only heating (no cooling), clamp to rated capacity
            Q_hp[t] = np.clip(Q_needed, 0.0, self.P_hp_max)

            # Update indoor temperature (forward Euler)
            T_in[t + 1] = T_in[t] + self.dt / self.C * (Q_hp[t] + self.Q_int - Q_loss)

        return Q_hp, T_in, cop
