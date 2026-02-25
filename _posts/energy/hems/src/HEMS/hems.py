"""
Main module for the Home Energy Management System (HEMS) project.

The :class:`HEMS` object owns a single CVXPY problem that is compiled
once and can be re-solved cheaply by updating parameter values only
(DPP-compliant warm-starting).

Cost model (NL dynamic electricity contracts)
----------------------------------------------
The consumer-facing electricity cost has several components:

.. math::

    \\text{import price}_t = (\\text{spot}_t + \\text{procurement}
    + \\text{energy tax}) \\times (1 + \\text{VAT})

    \\text{export price}_t = \\text{spot}_t + \\text{sell-back credit}

where **spot** is the day-ahead market price (time-varying parameter),
and the remaining terms are contract/regulatory constants.

Typical usage::

    hems = HEMS(
        loads=[base_load, hp],
        pvs=[solar],
        evs=[ev],
        battery=battery,
        price=spot_prices,
        procurement_fee=0.0248,      # Tibber
        sell_back_credit=0.0000,
        energy_tax=0.0916,           # NL 2025
        vat=0.21,
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

    Cost model (for ``"cost"`` objective)::

        import_price[t] = (spot[t] + procurement_fee + energy_tax) × (1 + vat)
        export_price[t] = spot[t] + sell_back_credit
        objective = min  Σ dt × (import_price[t] × P_import[t]
                                - export_price[t] × P_export[t])
    """

    # --- Supplier presets (NL, Feb 2026 tariffs) ------------------
    SUPPLIERS: dict[str, dict] = {
        "Tibber": {
            "procurement_fee": 0.0248,
            "sell_back_credit": 0.0000,
        },
        "Zonneplan": {
            "procurement_fee": 0.0200,
            "sell_back_credit": 0.0200,
        },
        "Frank Energie": {
            "procurement_fee": 0.0182,
            "sell_back_credit": 0.0182,
        },
    }

    def __init__(
        self,
        T: int | None = None,
        dt: float = DT_DEFAULT,
        # --- components (all optional) ---
        loads: Sequence[GenericLoad] | None = None,
        pvs: Sequence[Solar] | None = None,
        evs: Sequence[EV] | None = None,
        battery: Battery | None = None,
        # --- economic (NL cost model) ---
        price: np.ndarray | None = None,
        procurement_fee: float = 0.0,
        sell_back_credit: float = 0.0,
        energy_tax: float = 0.0,
        vat: float = 0.0,
        net_metering: bool = False,
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
            price: Day-ahead spot / market price [€/kWh], shape ``(T,)``.
                This is the **wholesale** price *before* any supplier
                markup, taxes, or VAT.
            procurement_fee: Supplier per-kWh markup on import [€/kWh].
            sell_back_credit: Per-kWh credit added to spot for
                exported electricity [€/kWh].
            energy_tax: Per-kWh energy tax on import [€/kWh]
                (NL: *energiebelasting*).
            vat: Value-added tax fraction applied to
                ``(spot + procurement_fee)`` on import (e.g. ``0.21``
                for 21 % BTW).
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

        # --- Cost model constants (baked into the compiled problem) ---
        self.procurement_fee = float(procurement_fee)
        self.sell_back_credit = float(sell_back_credit)
        self.energy_tax = float(energy_tax)
        self.vat = float(vat)
        self.net_metering = bool(net_metering)

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

        # --- Spot-price parameter (updated between daily solves) ---
        self.price = cp.Parameter(self.T, name="spot_EUR_kWh")
        if price is not None:
            self.price.value = np.asarray(price, dtype=float)
        else:
            self.price.value = np.zeros(self.T)

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

        For the **COST** objective the full NL-style cost model is used:

        .. math::

            \\text{import\\_price}_t =
                (\\text{spot}_t + \\text{procurement}
                + \\text{energy\\_tax})
                \\times (1 + \\text{vat})

            \\text{export\\_price}_t =
                \\text{spot}_t + \\text{sell\\_back\\_credit}

        A small battery cycling penalty (€/kWh throughput) is added to
        all objectives to prevent degenerate simultaneous or rapidly-
        alternating charge / discharge.  This represents battery
        degradation cost (~0.5 ct/kWh).

        Returns:
            CVXPY objective (Minimize or Maximize).
        """
        # Cycling penalty — prevents degenerate battery oscillation
        cycle_penalty = 0
        if self.battery is not None:
            cycle_penalty = (
                0.005 * self.dt * cp.sum(self.battery.P_ch + self.battery.P_dis)
            )

        if self.objective_type == Objective.COST:
            # import_price[t] = (spot[t] + procurement + energy_tax) * (1+vat)
            #                 = spot[t]*(1+vat) + (procurement+energy_tax)*(1+vat)
            vf = 1.0 + self.vat  # VAT multiplier
            import_adder = (self.procurement_fee + self.energy_tax) * vf  # €/kWh const

            cost_import = self.dt * (
                vf * (self.price @ self.P_import)  # time-varying
                + import_adder * cp.sum(self.P_import)  # constant per-kWh
            )

            # export_price[t] = spot[t] + sell_back_credit
            # (or import_price[t] if net metering is on)
            if self.net_metering:
                cost_export = self.dt * (
                    vf * (self.price @ self.P_export)
                    + import_adder * cp.sum(self.P_export)
                )
            else:
                cost_export = self.dt * (
                    self.price @ self.P_export
                    + self.sell_back_credit * cp.sum(self.P_export)
                )

            return cp.Minimize(cost_import - cost_export + cycle_penalty)

        elif self.objective_type == Objective.SELF_CONSUMPTION:
            # max Σ (PV used locally) = max Σ (P_pv - P_export)
            # When PV is curtailable, P_pv is a variable so the
            # objective incentivises generating *and* using PV locally.
            pv_total = 0
            for pv in self.pvs:
                pv_total += cp.sum(pv.P)
            return cp.Maximize(
                self.dt * (pv_total - cp.sum(self.P_export)) - cycle_penalty
            )

        elif self.objective_type == Objective.SELF_RELIANCE:
            # min Σ P_import
            return cp.Minimize(self.dt * cp.sum(self.P_import) + cycle_penalty)

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
            dict with keys:

            - ``status`` – solver status string
            - ``cost`` – net energy cost [€] (objective value)
            - ``cost_import`` – total import cost [€]
            - ``cost_export`` – total export revenue [€]
            - ``P_import`` – import power profile [kW]
            - ``P_export`` – export power profile [kW]

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

        imp = self.P_import.value.copy()
        exp = self.P_export.value.copy()
        spot = self.price.value

        # --- Compute cost breakdown ---
        if self.objective_type == Objective.COST:
            vf = 1.0 + self.vat
            ia = (self.procurement_fee + self.energy_tax) * vf
            cost_import = float(self.dt * (vf * (spot @ imp) + ia * np.sum(imp)))
            if self.net_metering:
                cost_export = float(self.dt * (vf * (spot @ exp) + ia * np.sum(exp)))
            else:
                cost_export = float(
                    self.dt * (spot @ exp + self.sell_back_credit * np.sum(exp))
                )
        else:
            # For non-cost objectives, report raw spot costs only
            cost_import = float(self.dt * (spot @ imp))
            cost_export = float(self.dt * (spot @ exp))

        return {
            "status": self.problem.status,
            "cost": float(self.problem.value),
            "cost_import": cost_import,
            "cost_export": cost_export,
            "P_import": imp,
            "P_export": exp,
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
            self.battery.E_0.value = float(self.battery.E.value[-1])

        for ev in self.evs:
            if ev.E.value is not None:
                ev.E_0.value = float(ev.E.value[-1])

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
        """Return a human-readable summary of the last solve.

        Includes a cost breakdown when the objective is ``COST``.
        """
        if self.problem.status is None:
            return "Problem has not been solved yet."

        imp = self.P_import.value
        exp = self.P_export.value
        spot = self.price.value
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

        # --- Cost breakdown (COST objective) ---
        if self.objective_type == Objective.COST:
            vf = 1.0 + self.vat
            import_kwh = np.sum(imp) * self.dt
            export_kwh = np.sum(exp) * self.dt

            spot_import = self.dt * (spot @ imp)
            proc_cost = self.procurement_fee * import_kwh
            tax_cost = self.energy_tax * import_kwh
            subtotal = spot_import + proc_cost + tax_cost
            vat_import = self.vat * subtotal
            total_import = subtotal + vat_import

            spot_export = self.dt * (spot @ exp)
            sbc_export = self.sell_back_credit * export_kwh
            total_export = spot_export + sbc_export

            lines += [
                "",
                "  --- Cost breakdown (import) ---",
                f"  Spot × import : € {spot_import:7.4f}",
                f"  + Procurement : € {proc_cost:7.4f}  "
                f"({self.procurement_fee:.4f} €/kWh)",
                f"  + Energy tax  : € {tax_cost:7.4f}  ({self.energy_tax:.4f} €/kWh)",
                f"  + VAT ({self.vat * 100:.0f}%)    : € {vat_import:7.4f}  "
                f"(on all above)",
                f"  = Import cost : € {total_import:7.4f}",
                "  --- Cost breakdown (export) ---",
                f"  + Sell-back   : € {sbc_export:7.4f}  "
                f"({self.sell_back_credit:.4f} €/kWh)",
                f"  = Export rev. : € {total_export:7.4f}",
                f"  Net cost      : € {total_import - total_export:7.4f}",
            ]
        return "\n".join(lines)
