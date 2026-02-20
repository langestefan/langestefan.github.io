"""
Implementation of loads for the HEMS system.
"""

import cvxpy as cp
import numpy as np
from HEMS.battery import Battery


class EV(Battery):
    """An electric vehicle load that can be scheduled for charging.

    This class represents an electric vehicle with controllable charging/discharging
    capabilities. It extends ``Battery`` with EV-specific behaviour: trip energy
    consumption and time-dependent availability (the EV can only charge/discharge
    when it is at home).
    """

    def __init__(
        self,
        T: int,
        dt: float = 0.25,
        name: str = "EV",
        E_max: float = 50.0,
        P_ch_max: float = 7.0,
        P_dis_max: float = 0.0,
        eta_ch: float = 0.9,
        eta_dis: float = 0.9,
    ):
        """Initialize an electric vehicle load.

        We make the following assumptions for the EV:
        - The EV can only charge when it is at home (between arrival and depart times).
        - By default the EV cannot discharge (P_dis_max = 0), but this can be modified
          if V2G capabilities are desired.
        - The energy consumed during trips is modeled as a fixed energy consumption at
          the departure time, which reduces the state of charge (SoC) of the battery.

        Args:
            T (int): Time horizon (number of time steps).
            dt (float): Time step duration in hours (default 0.25 = 15 min).
            name (str): Name identifier for the EV.
            E_max (float): Maximum battery capacity in kWh.
            P_ch_max (float): Maximum charging power in kW.
            P_dis_max (float): Maximum discharging power in kW.
            eta_ch (float): Charging efficiency (0-1).
            eta_dis (float): Discharging efficiency (0-1).
        """
        super().__init__(T, dt, name, E_max, P_ch_max, P_dis_max, eta_ch, eta_dis)

        # Alias the inherited E_drain parameter as trip energy for readability
        self.u = self.E_drain
        self.u.value = np.zeros(T)

        # Availability: 1 = EV at home, 0 = EV away
        self.a = cp.Parameter(T, nonneg=True, name=f"{name}_Availability")
        self.a.value = np.ones(T)

        # Override initial/terminal SoC defaults for a typical EV
        self.E_0.value = 20.0
        self.E_T.value = 20.0

        # Schedule default trips
        self.schedule_trips()

    def schedule_trips(
        self, trips: list[tuple[int, int, float]] = [(8 * 4, 18 * 4, 10.0)]
    ):
        """Schedule EV trips.

        Sets trip energy consumption and marks unavailability windows.

        Args:
            trips: List of (departure_step, arrival_step, energy_consumed_kWh).
        """
        self.u.value = np.zeros(self.T)  # Reset trip energy
        self.a.value = np.ones(self.T)  # Reset availability

        # set energy consumed at departure and mark unavailability during trips
        for departure_time, arrival_time, energy_consumed in trips:
            if 0 <= departure_time < self.T:
                self.u.value[departure_time] = energy_consumed  # type: ignore
                self.a.value[departure_time:arrival_time] = 0  # type: ignore

    def constraints(self) -> list:
        """Return the CVXPY constraints for the EV.

        Extends the base ``Battery`` constraints with availability-based
        power limits.  All constraints are DPP-compliant: parameters
        (self.a, self.u) appear only as coefficients; variables (P_ch,
        P_dis, E, z) appear linearly throughout.

        Returns:
            list: List of CVXPY constraints.
        """
        # Start from the core battery constraints (SoC dynamics already
        # include the trip energy via the inherited E_drain parameter).
        constraints = super().constraints()

        # --- Power limits with availability ---
        # Availability is enforced via separate linear inequalities so that the
        # product a[t]*z[t] (parameter * variable) never appears — keeping DPP.
        #   P_ch[t] <= P_ch_max * a[t]           (a=0 blocks charging when away)
        #   P_dis[t] <= P_dis_max * a[t]          (a=0 blocks discharging when away)
        constraints += [
            self.P_ch <= cp.multiply(self.a, np.full(self.T, self.P_ch_max))
        ]
        constraints += [
            self.P_dis <= cp.multiply(self.a, np.full(self.T, self.P_dis_max))
        ]

        return constraints
