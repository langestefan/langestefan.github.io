"""
Implementation of battery model for the HEMS system.
"""

import cvxpy as cp
import numpy as np
from HEMS.base import FlexibleLoad

from .const import DT_DEFAULT


class Battery(FlexibleLoad):
    """A battery model representing an energy storage system in the HEMS.

    This class models a battery with charging and discharging capabilities,
    state of charge dynamics, and constraints on power and energy levels.
    It inherits from FlexibleLoad so that the net power variable ``P``
    participates directly in the HEMS optimisation.

    The SoC dynamics include an external energy drain parameter
    ``E_drain`` (defaults to zero) that subclasses (e.g. EV) can use to
    model additional energy losses such as trip consumption.
    """

    def __init__(
        self,
        T: int,
        dt: float = DT_DEFAULT,
        name: str = "Battery",
        E_max: float = 13.5,
        P_ch_max: float = 5.0,
        P_dis_max: float = 5.0,
        eta_ch: float = 0.95,
        eta_dis: float = 0.95,
    ):
        """Initialize the battery model.

        Args:
            T (int): Time horizon (number of time steps).
            dt (float): Duration of each time step in hours (default: 0.25 for 15-minute intervals).
            name (str): Name identifier for the battery.
            E_max (float): Maximum energy capacity in kWh.
            P_ch_max (float): Maximum charging power in kW.
            P_dis_max (float): Maximum discharging power in kW.
            eta_ch (float): Charging efficiency (0-1).
            eta_dis (float): Discharging efficiency (0-1).
        """
        super().__init__(name, T)
        self.dt = dt
        self.E_max = E_max
        self.P_ch_max = P_ch_max
        self.P_dis_max = P_dis_max
        self.eta_ch = eta_ch
        self.eta_dis = eta_dis

        # State of charge [kWh], size T+1 to include both endpoints
        self.E = cp.Variable(T + 1, nonneg=True, name=f"{name}_SoC_kWh")

        # Charging and discharging power [kW]
        self.P_ch = cp.Variable(T, nonneg=True, name=f"{name}_P_ch_kW")
        self.P_dis = cp.Variable(T, nonneg=True, name=f"{name}_P_dis_kW")

        # Binary mode: z[t]=1 => charging allowed, z[t]=0 => discharging allowed
        self.z = cp.Variable(T, boolean=True, name=f"{name}_Mode")

        # Initial and terminal state of charge [kWh]
        self.E_0 = cp.Parameter(nonneg=True, name=f"{name}_E0_kWh", value=E_max / 2)
        self.E_T = cp.Parameter(nonneg=True, name=f"{name}_ET_kWh", value=E_max / 2)

        # External energy drain per timestep [kWh] — subclasses (e.g. EV)
        # can set this to model additional losses such as trip consumption.
        self.E_drain = cp.Parameter(T, nonneg=True, name=f"{name}_drain_kWh")
        self.E_drain.value = np.zeros(T)

    def constraints(self) -> list:
        """Return the CVXPY constraints for the battery.

        All constraints are DPP-compliant: parameters appear only as
        coefficients or RHS constants; variables appear linearly.

        Returns:
            list: List of CVXPY constraints.
        """
        constraints: list = []

        # --- Initial condition ---
        constraints += [self.E[0] == self.E_0]

        # --- SoC dynamics ---
        # E[t+1] = E[t] + dt*(eta_ch*P_ch[t] - P_dis[t]/eta_dis) - E_drain[t]
        constraints += [
            self.E[1:]
            == self.E[:-1]
            + self.dt * (self.eta_ch * self.P_ch - (1.0 / self.eta_dis) * self.P_dis)
            - self.E_drain
        ]

        # --- Energy bounds ---
        constraints += [self.E >= 0, self.E <= self.E_max]

        # --- Terminal SoC ---
        constraints += [self.E[self.T] >= self.E_T]

        # --- Power limits with no simultaneous charge/discharge ---
        constraints += [self.P_ch <= self.P_ch_max * self.z]
        constraints += [self.P_dis <= self.P_dis_max * (1 - self.z)]

        # --- Net power seen by the grid (positive = consuming) ---
        constraints += [self.P == self.P_ch - self.P_dis]

        return constraints
