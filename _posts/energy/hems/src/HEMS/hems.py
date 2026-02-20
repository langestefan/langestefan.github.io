"""
Main module for the Home Energy Management System (HEMS) project.

The :class:`HEMS` object owns a single CVXPY problem that is compiled
once and can be re-solved cheaply by updating parameter values only
(DPP-compliant warm-starting).

Typical usage::

    hems = HEMS(
        loads=[base_load, hp],
        pvs=[solar],
        evs=[ev],
        battery=battery,
        price=price_signal,
        objective="cost",
    )

    # Rolling-horizon loop
    for step_idx in range(N_steps):
        update_parameters(...)      # e.g. new price, new solar forecast
        result = hems.solve()       # re-solve with updated parameters
        hems.step()                 # advance initial conditions
"""

from __future__ import annotations

from enum import Enum
from typing import Sequence

import cvxpy as cp
import numpy as np

from .base import GenericLoad
from .battery import Battery
from .const import DT_DEFAULT
from .load import EV
from .solar import Solar


class Objective(str, Enum):
    """Optimisation objective for the HEMS."""

    COST = "cost"
    """Minimise total electricity cost (grid import × price)."""

    SELF_CONSUMPTION = "self_consumption"
    """Maximise self-consumption of locally generated PV power."""

    SELF_RELIANCE = "self_reliance"
    """Minimise total grid import (maximise self-reliance)."""


class HEMS:
    """Home Energy Management System coordinating loads, PV, EVs and battery.

    The constructor builds a complete CVXPY problem that is verified to be
    both DCP and DPP.  Because the problem is DPP-compliant, parameter
    values can be updated efficiently between solves without recompiling
    the problem.

    Power-balance convention (positive = consuming from the grid)::

        P_grid[t] = Σ P_load[t] + Σ P_ev[t] + P_bat[t] - Σ P_pv[t]
        P_grid = P_import - P_export        (both ≥ 0)
    """

    def __init__(
        self,
        T: int | None = None,
        dt: float = DT_DEFAULT,
        # --- components (all optional) ---
        loads: Sequence[GenericLoad] | None = None,
        pvs: Sequence[Solar] | None = None,
        evs: Sequence[EV] | None = None,
        battery: Battery | None = None,
        # --- economic ---
        price: np.ndarray | None = None,
        feed_in_price: np.ndarray | float = 0.0,
        # --- objective ---
        objective: str | Objective = Objective.COST,
        # --- solver ---
        solver: str = cp.HIGHS,
    ):
        """Initialise the HEMS and compile the CVXPY problem.

        All component lists are optional — pass only what exists in the
        household.  The time horizon *T* is inferred from the first
        component found (loads → pvs → evs → battery); if no components
        are supplied, *T* must be given explicitly.

        Args:
            T: Number of time steps.  Inferred from components if ``None``.
            dt: Duration of each time step [h].
            loads: Fixed or flexible loads (e.g. :class:`HeatPump`,
                :class:`BaseLoad`).
            pvs: PV arrays (:class:`Solar`).  Their ``P`` represents
                generation injected into the home.
            evs: Electric vehicles (:class:`EV`).
            battery: A single :class:`Battery` (home storage).
            price: Electricity import price [€/kWh], shape ``(T,)``.
                Required for ``"cost"`` objective.
            feed_in_price: Feed-in tariff [€/kWh].  Scalar or ``(T,)`` array.
            objective: Optimisation goal — ``"cost"``,
                ``"self_consumption"``, or ``"self_reliance"``.
            solver: CVXPY solver name.
        """
        # --- Normalise inputs ---
        self.loads: list[GenericLoad] = list(loads) if loads else []
        self.pvs: list[Solar] = list(pvs) if pvs else []
        self.evs: list[EV] = list(evs) if evs else []
        self.battery: Battery | None = battery
        self.solver = solver
        self.dt = dt
        self.objective_type = Objective(objective)

        # --- Infer T ---
        all_components: list[GenericLoad] = (
            self.loads + self.pvs + self.evs  # type: ignore[operator]
        )
        if battery is not None:
            all_components.append(battery)

        if T is not None:
            self.T = T
        elif all_components:
            self.T = all_components[0].T
        else:
            raise ValueError("Cannot infer T: no components supplied and T is None.")

        # Validate that all components share the same T
        for comp in all_components:
            if comp.T != self.T:
                raise ValueError(
                    f"Component '{comp.name}' has T={comp.T}, expected T={self.T}."
                )

        # --- Price parameters ---
        self.price = cp.Parameter(self.T, nonneg=True, name="price_EUR_kWh")
        if price is not None:
            self.price.value = np.asarray(price, dtype=float)
        else:
            self.price.value = np.zeros(self.T)

        feed_in = np.broadcast_to(
            np.asarray(feed_in_price, dtype=float), (self.T,)
        ).copy()
        self.feed_in_price = cp.Parameter(self.T, nonneg=True, name="feed_in_EUR_kWh")
        self.feed_in_price.value = feed_in

        # --- Grid power split ---
        self.P_import = cp.Variable(self.T, nonneg=True, name="P_import_kW")
        self.P_export = cp.Variable(self.T, nonneg=True, name="P_export_kW")

        # --- Build constraints ---
        constraints: list = []

        # Power balance:
        #   P_import - P_export = Σ loads + Σ EVs + battery - Σ PVs
        P_demand = 0
        for load in self.loads:
            P_demand += load.P
        for ev in self.evs:
            P_demand += ev.P
        if self.battery is not None:
            P_demand += self.battery.P  # positive = charging = consuming

        P_generation = 0
        for pv in self.pvs:
            P_generation += pv.P

        constraints += [self.P_import - self.P_export == P_demand - P_generation]

        # Component constraints
        for load in self.loads:
            if hasattr(load, "constraints"):
                constraints += load.constraints()
        for pv in self.pvs:
            constraints += pv.constraints()
        for ev in self.evs:
            constraints += ev.constraints()
        if self.battery is not None:
            constraints += self.battery.constraints()

        self._constraints = constraints

        # --- Build objective ---
        obj_expr = self._build_objective()
        self._objective = obj_expr

        # --- Compile problem ---
        self.problem = cp.Problem(obj_expr, constraints)

        if not self.problem.is_dcp():
            raise ValueError("HEMS problem is not DCP compliant.")
        if not self.problem.is_dpp():
            raise ValueError("HEMS problem is not DPP compliant.")

    # ------------------------------------------------------------------
    # Objective construction
    # ------------------------------------------------------------------

    def _build_objective(self) -> cp.Minimize | cp.Maximize:
        """Construct the CVXPY objective expression.

        Returns:
            CVXPY objective (Minimize or Maximize).
        """
        if self.objective_type == Objective.COST:
            # min  Σ dt * (price * P_import  -  feed_in * P_export)
            cost_import = self.dt * (self.price @ self.P_import)
            cost_export = self.dt * (self.feed_in_price @ self.P_export)
            return cp.Minimize(cost_import - cost_export)

        elif self.objective_type == Objective.SELF_CONSUMPTION:
            # max Σ (PV used locally) = max Σ (P_pv - P_export)
            # When PV is curtailable, P_pv is a variable so the
            # objective incentivises generating *and* using PV locally.
            pv_total = 0
            for pv in self.pvs:
                pv_total += cp.sum(pv.P)
            return cp.Maximize(self.dt * (pv_total - cp.sum(self.P_export)))

        elif self.objective_type == Objective.SELF_RELIANCE:
            # min Σ P_import
            return cp.Minimize(self.dt * cp.sum(self.P_import))

        else:
            raise ValueError(f"Unknown objective: {self.objective_type}")

    # ------------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------------

    def solve(self, **kwargs) -> dict:
        """Solve (or re-solve) the HEMS optimisation problem.

        Because the problem is DPP-compliant, updating parameter values
        and calling :meth:`solve` again re-uses the compiled problem
        structure for fast re-solves.

        Args:
            **kwargs: Extra keyword arguments forwarded to
                ``cp.Problem.solve()`` (e.g. ``verbose=True``).

        Returns:
            dict: Summary with keys ``status``, ``cost``, ``P_import``,
            ``P_export``.

        Raises:
            RuntimeError: If the solver reports an infeasible or
            unbounded status.
        """
        kwargs.setdefault("solver", self.solver)
        self.problem.solve(**kwargs)

        if self.problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            raise RuntimeError(
                f"HEMS optimisation failed: status={self.problem.status}"
            )

        return {
            "status": self.problem.status,
            "cost": self.problem.value,
            "P_import": self.P_import.value.copy(),
            "P_export": self.P_export.value.copy(),
        }

    # ------------------------------------------------------------------
    # Step (rolling horizon)
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance initial conditions by one time step after a solve.

        Updates the ``E_0`` (initial SoC) parameters of the battery
        and all EVs to reflect the SoC at ``t=1`` from the last solve.
        This is intended for rolling-horizon operation where the problem
        is re-solved at each step with shifted parameters.

        Call this *after* :meth:`solve` and *before* updating parameters
        for the next horizon.
        """
        if self.battery is not None and self.battery.E.value is not None:
            self.battery.E_0.value = float(self.battery.E.value[1])

        for ev in self.evs:
            if ev.E.value is not None:
                ev.E_0.value = float(ev.E.value[1])

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def total_pv_generation(self) -> np.ndarray:
        """Total PV generation across all arrays [kW], shape ``(T,)``."""
        total = np.zeros(self.T)
        for pv in self.pvs:
            if isinstance(pv.P, cp.Variable):
                if pv.P.value is not None:
                    total += pv.P.value
            else:
                if pv.P.value is not None:
                    total += pv.P.value
        return total

    @property
    def total_load(self) -> np.ndarray:
        """Total non-EV load consumption [kW], shape ``(T,)``."""
        total = np.zeros(self.T)
        for load in self.loads:
            if isinstance(load.P, cp.Variable):
                if load.P.value is not None:
                    total += load.P.value
            else:
                if load.P.value is not None:
                    total += load.P.value
        return total

    @property
    def total_ev_load(self) -> np.ndarray:
        """Total EV net power [kW], shape ``(T,)``."""
        total = np.zeros(self.T)
        for ev in self.evs:
            if ev.P.value is not None:
                total += ev.P.value
        return total

    def summary(self) -> str:
        """Return a human-readable summary of the last solve."""
        if self.problem.status is None:
            return "Problem has not been solved yet."

        imp = self.P_import.value
        exp = self.P_export.value
        lines = [
            f"HEMS Summary  (objective={self.objective_type.value})",
            f"  Status       : {self.problem.status}",
            f"  Obj. value   : {self.problem.value:.4f}",
            f"  Grid import  : {np.sum(imp) * self.dt:.1f} kWh  "
            f"(peak {imp.max():.2f} kW)",
            f"  Grid export  : {np.sum(exp) * self.dt:.1f} kWh  "
            f"(peak {exp.max():.2f} kW)",
        ]
        if self.pvs:
            pv_total = np.sum(self.total_pv_generation) * self.dt
            lines.append(f"  PV generation: {pv_total:.1f} kWh")
            self_consumed = pv_total - np.sum(exp) * self.dt
            lines.append(
                f"  Self-consumed: {self_consumed:.1f} kWh  "
                f"({self_consumed / max(pv_total, 1e-9) * 100:.1f}%)"
            )
        if self.battery is not None and self.battery.E.value is not None:
            lines.append(
                f"  Battery SoC  : {self.battery.E.value[0]:.1f} → "
                f"{self.battery.E.value[-1]:.1f} kWh"
            )
        for ev in self.evs:
            if ev.E.value is not None:
                lines.append(
                    f"  {ev.name} SoC   : {ev.E.value[0]:.1f} → "
                    f"{ev.E.value[-1]:.1f} kWh"
                )
        return "\n".join(lines)
