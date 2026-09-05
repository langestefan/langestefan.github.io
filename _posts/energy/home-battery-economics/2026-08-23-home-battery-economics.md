---
layout: distill
title: Home Battery Economics through Simulation
# description: What a home battery actually earns back under Dutch dynamic electricity pricing, simulated against real day-ahead prices
description: A simulation-based analysis to explore robust and sustainable strategies for home energy storage under (future) dynamic electricity pricing.
tags: energy battery storage economics simulation
categories: energy
giscus_comments: true
date: 2026-08-23
featured: true
published: false
toc:
  - name: Summary
  - name: The Model
  - name: The Dispatch Problem
  - name: Asset Models
  - name: Exogenous Inputs
  - name: Prices, Tariffs and Settlement
  - name: Investment Metrics
  - name: Simulation Setup
  - name: Results
  - name: Sensitivity
  - name: Conclusion
authors:
  - name: Stefan de Lange
    affiliations:
      name: TU Eindhoven
---

## Summary

---

## What is a HEMS?

Before we explain how the model is constructed, we need to understand what a HEMS is. If
you are already familiar with the concept, feel free to skip this section.

HEMS stands for Home Energy Management System. It is an abstract term that can mean many
things, which makes it a confusing concept. In this article, we will use the term HEMS
to refer to a system that fulfills our (perhaps specific) requirements for this study,
explained in this section.

A HEMS is a system that has monitoring, control and forecast capabilities and can deploy
these in such a way that they are complimentary functions and new capabilities emerge.
For example, a HEMS can forecast household energy consumption if proper monitoring is in
place. It can then use those forecasts to control assets, considering future energy
flows in the home. A non-exhaustive list of the capabilities of a HEMS is as follows:

- Monitor both energy consumption and production at the interface to the grid (i.e. the
  electricity meter)
- Can estimate variables that cannot be measured directly, such as the power consumption
  of the household.
- Can _monitor_ and _control_ the most important energy assets in the household. We
  consider here only the "big 4": the battery, the solar PV system, the heat pump and the
  electric vehicle. {% sidenote %}Not every household needs to have all of these assets.
  Control of PV and heat pump is not strictly necessary for optimal operation of the HEMS.
  A HEMS also does not strictly need a battery to be able to control the other assets.{% endsidenote %}

The diagram below shows all the pieces of the HEMS and how they interact with each
other. The HEMS is the central piece of the system.

<div class="l-page">
  <figure>{% include_relative hems-block-diagram.svg %}</figure>
</div>

### Assumptions

To make the problem computationally feasible, we make a number of assumptions. These
assumptions are not necessarily unrealistic for a real system, but if they are not met,
the results of this study may not be applicable to your situation. The assumptions are
as follows:

- The HEMS has perfect knowledge of the future. This means that it knows exactly what the
  household load will be, what the PV production will be, and what the electricity prices
  will be. In reality, this is not possible, but we can use forecasts to approximate this
  knowledge.
- The HEMS has perfect control of the most important assets. This means that commands
  that are sent to the EV, heatpump, battery and PV system are always executed perfectly.
  In reality, this may not always be the case.
- Simulating a 'real' EV charger is difficult without realitic departure / arrival times,
  so we assume a fixed schedule for the EV outside the weekend. During the weekend, the
  EV is assumed to be at home all day.
- We use a receding horizon controller, running at a fixed interval of 15 minutes. The
  horizon interval is also 15 minutes, and control actions are piecewise constant over
  each interval. A power limit constraint is therefore a constraint over the 15-minute
  average power, and not on the instantaneous power. This can be unrealistic for loads
  that have a high peak power but low energy consumption over an interval.

## The Optimization Model

Our controller is a linear program (LP) that optimizes the operation of the household
assets over a receding horizon. The LP is solved repeatedly, and the first control action
is implemented. The LP is then solved again with updated information, and the process
repeats.

The diagram below shows how the window moves. Each solve looks $$W$$ intervals ahead but
only the first interval is ever executed. After executing the first step the window then 
slides forward by 1. Whatever the assets' state at the end of the previous step was 
becomes the initial conditions for the current step. We repeat this process until we hit 
the end of the simulation.

<div class="l-page">
  <figure>{% include_relative receding-horizon-diagram.svg %}</figure>
</div>

### Notation

We divide the horizon into $$n$$ intervals of $$\Delta$$ hours each, indexed by
$$k = 1, \dots, n$$. The simulations in this article use $$\Delta = 0.25\,\mathrm{h}$$.
All variables and parameters are indexed by $$k$$, the interval number. The following
table lists the symbols used in the model, their meaning and their units.

| Symbol                                          | Meaning                               | Unit  |
| :---------------------------------------------- | :------------------------------------ | :---- |
| $$\Delta$$                                      | interval length                       | h     |
| $$g^{\mathrm{imp}}_k, g^{\mathrm{exp}}_k$$      | energy taken from / fed into the grid | kW    |
| $$P^{\mathrm{pv}}_k$$                           | PV power available before curtailment | kW    |
| $$c_k$$                                         | PV power curtailed                    | kW    |
| $$L_k$$                                         | household base load                   | kW    |
| $$\pi^{\mathrm{buy}}_k, \pi^{\mathrm{sell}}_k$$ | dispatch price signal                 | €/kWh |
| $$\theta_k$$                                    | ambient temperature                   | °C    |
| $$G_k$$                                         | global horizontal irradiance          | W/m²  |

---

## The Dispatch Problem

### The meter balance

Every interval must balance at the electricity meter. This single equality is the only
thing coupling the assets to each other:

$$
g^{\mathrm{imp}}_k - g^{\mathrm{exp}}_k + P^{\mathrm{pv}}_k - c_k + \sum_{a \in \mathcal{A}} v_{a,k}
\;=\;
L_k + \sum_{a \in \mathcal{A}} u_{a,k}
\qquad k = 1, \dots, n
$$

subject to the physical connection limit $$P^{\mathrm{conn}}$$ and the fact that you cannot
curtail solar you never had:

$$
0 \leq g^{\mathrm{imp}}_k \leq P^{\mathrm{conn}},
\qquad
0 \leq g^{\mathrm{exp}}_k \leq P^{\mathrm{conn}},
\qquad
0 \leq c_k \leq P^{\mathrm{pv}}_k .
$$

The default $$P^{\mathrm{conn}} = 17.3\,\mathrm{kW}$$ corresponds to a Dutch 3×25 A
connection. Note that import and export are separate non-negative variables rather than one
signed flow: they are priced differently, so the sign matters to the objective and cannot be
recovered afterwards.

### The objective

The controller minimises a weighted sum of imported energy and money over the window:

$$
\min \quad
\sum_{k=1}^{n} \Delta \Big[\, w_E\, g^{\mathrm{imp}}_k
\;+\; w_C \big( \pi^{\mathrm{buy}}_k g^{\mathrm{imp}}_k - \pi^{\mathrm{sell}}_k g^{\mathrm{exp}}_k \big) \Big]
\;+\; w_C \sum_{a \in \mathcal{A}} C_a
\;+\; J^{\mathrm{tb}}
$$

where $$C_a$$ is the asset's own objective contribution — throughput cost, comfort
penalties, terminal storage value — defined per asset below.

A **strategy** is nothing more than the pair $$(w_E, w_C)$$. The model is otherwise
identical, which is the point: two strategies are comparable because nothing else differs.

$$
\text{Economic:} \quad (w_E, w_C) = (0, 1),
\qquad\qquad
\text{Green:} \quad (w_E, w_C) = (1, 10^{-3}).
$$

Under the green strategy self-consumption is not imposed, it _falls out_. Charging the
battery from the grid is itself an import, and a round trip loses energy, so it can never
avoid as much later import as it costs now — an import-minimising optimizer therefore never
grid-charges. The small cost weight is a tie-break that picks the cheapest of the many
schedules that import equally little.

The last term breaks ties towards acting **earlier**:

$$
J^{\mathrm{tb}} = \varepsilon_{\mathrm{tb}}\, \Delta \sum_{k=1}^{n} (k-1)
\Big( g^{\mathrm{imp}}_k + \sum_{a \in \mathcal{A}} u_{a,k} \Big),
\qquad \varepsilon_{\mathrm{tb}} = 10^{-6}\ \text{€/kWh per interval of delay}.
$$

{% sidenote %}This is not cosmetic. Step-holding an hourly price onto quarter-hours makes
more than half of 2025's adjacent intervals _exactly_ equal, so the LP genuinely has many
optima and the solver picks one arbitrarily. The controller cannot tell the difference; the
settlement engine can, because it reads the flows rather than the objective. Its size is
squeezed from both ends — large enough to clear the solver's dual-feasibility tolerance,
small enough to stay below the smallest real price difference between neighbouring
intervals.{% endsidenote %}

### Receding horizon

The problem above is solved repeatedly on a moving window rather than once over the year.
With a window of $$W$$ intervals and a step of $$S \leq W$$ intervals, the controller solves
over $$[t,\, t + W)$$, implements only the first $$S$$ intervals, carries each asset's
terminal state into the next solve, and advances to $$t + S$$.

The overlap is what stops the optimizer emptying its storage at every window boundary. A
year at $$W = 48\,\mathrm{h}$$ and $$S = 24\,\mathrm{h}$$ is 366 solves; the realistic
controller, re-optimising every quarter-hour ($$S = 1$$), is 35 040.

### Degeneracy and the exclusivity option

The linear program keeps a battery from charging and discharging at once, and keeps the
meter from importing and exporting at once, only because doing both wastes energy and
wasting energy costs money. Two situations break that assumption.

Under full net metering the buy and sell prices are equal, so a simultaneous import and
export is free. A small forced spread $$\varepsilon_\pi$$ (subtracted from the sell price,
see below) restores uniqueness at no cost in accuracy, because the reported bill comes from
the settlement engine rather than from this objective.

Under **negative prices** — routine on the Dutch day-ahead market — burning energy is
genuinely profitable, and no price nudge fixes that. It needs binaries. For any asset with
both a charge and a discharge variable, introduce $$z_k \in \{0,1\}$$ and

$$
u_{a,k} \leq \overline{U}_a\, z_k,
\qquad
v_{a,k} \leq \overline{V}_a\, (1 - z_k),
$$

which turns the LP into a MILP. It is off by default and the solver output is checked for
simultaneous flows, so a scenario that needs it announces itself rather than silently
reporting impossible dispatch.

---

## Asset Models

### Home battery

State of charge $$E_k$$ in kWh, charge power $$p^{\mathrm{ch}}_k$$ and discharge power
$$p^{\mathrm{dis}}_k$$ in kW:

$$
E_k = E_{k-1}
+ \Delta \left( \eta^{\mathrm{ch}} p^{\mathrm{ch}}_k - \frac{p^{\mathrm{dis}}_k}{\eta^{\mathrm{dis}}} \right)
- \Delta\, \gamma\, \overline{E},
\qquad E_0 = \sigma_{\mathrm{init}} \overline{E}
$$

$$
0 \leq p^{\mathrm{ch}}_k \leq \overline{P}^{\mathrm{ch}},
\qquad
0 \leq p^{\mathrm{dis}}_k \leq \overline{P}^{\mathrm{dis}},
\qquad
\sigma_{\min} \overline{E} \leq E_k \leq \sigma_{\max} \overline{E}
$$

with $$\overline{E}$$ the nameplate capacity in kWh and $$\gamma$$ the self-discharge as a
fraction of capacity per hour. The one-way efficiencies $$\eta^{\mathrm{ch}}$$ and
$$\eta^{\mathrm{dis}}$$ default to 0.95 each, so the round trip is
$$\eta^{\mathrm{ch}}\eta^{\mathrm{dis}} \approx 0.90$$. The asymmetry in the dynamics is
deliberate: charging is derated on the way in, discharging is inflated on the way out, so
both losses are charged against the battery rather than against the meter.

Its contribution to the objective is throughput cost plus terminal value:

$$
C_{\mathrm{bat}}
= \Delta\, c_{\mathrm{deg}} \sum_{k=1}^{n} \big( p^{\mathrm{ch}}_k + p^{\mathrm{dis}}_k \big)
\;-\; \lambda\, E_n,
\qquad
\lambda = \eta^{\mathrm{dis}} \cdot \operatorname{median}_k \big( \pi^{\mathrm{buy}}_k \big) .
$$

The degradation cost $$c_{\mathrm{deg}}$$ (€/kWh of throughput) is what makes the optimizer
trade cycling against arbitrage margin. The terminal term values energy left in the battery
at what it can displace later; without it the receding horizon empties the battery at every
window boundary. Valuing it at the window's _median_ buy price is deliberately conservative
— it never pays to store energy the optimizer could not plausibly recover.

Meter coupling: $$u_{\mathrm{bat},k} = p^{\mathrm{ch}}_k$$ and
$$v_{\mathrm{bat},k} = p^{\mathrm{dis}}_k$$.

### Electric vehicle

An EV is not a second battery. It is away when the sun is up on exactly the days its owner
commutes, it must be full enough to leave in the morning, and — unless V2G is enabled —
energy that goes into it never comes back out to the house.

Let $$\delta_k \in \{0,1\}$$ indicate that the car is plugged in, $$d_k \geq 0$$ be the
driving energy consumed in interval $$k$$ (kWh), and $$T_k$$ be a departure target (kWh,
zero except on the last connected interval before each departure). Then

$$
E_k = E_{k-1}
+ \Delta \left( \eta^{\mathrm{ch}} p^{\mathrm{ch}}_k - \frac{p^{\mathrm{dis}}_k}{\eta^{\mathrm{dis}}} \right)
- d_k
$$

$$
0 \leq p^{\mathrm{ch}}_k \leq \delta_k \overline{P}^{\mathrm{ch}},
\qquad
0 \leq p^{\mathrm{dis}}_k \leq \delta_k \overline{P}^{\mathrm{dis}},
\qquad
0 \leq E_k \leq \sigma_{\max} \overline{E}
$$

$$
E_k \geq \sigma_{\min} \overline{E} \quad \text{whenever } \delta_k = 1,
\qquad\qquad
E_k \geq T_k \quad \text{whenever } T_k > 0 .
$$

Three details separate this from the battery. The state-of-charge floor binds only while
the car is plugged in — it is a charging policy, not a physical limit, and enforcing it on
the road would make an otherwise reasonable trip infeasible. The target is a **deadline**
attached to a single interval rather than a floor held all night, which is precisely what
makes the charging flexible and the departure not. And $$\overline{P}^{\mathrm{dis}} = 0$$
by default, which disables V2G and leaves the car a pure sink.

The objective contribution carries throughput cost, but terminal value **only with V2G**:

$$
C_{\mathrm{ev}}
= \Delta\, c_{\mathrm{deg}} \sum_{k=1}^{n} \big( p^{\mathrm{ch}}_k + p^{\mathrm{dis}}_k \big)
\;-\; \mathbb{1}\big[\overline{P}^{\mathrm{dis}} > 0\big]\, \lambda\, E_n .
$$

{% sidenote %}The asymmetry with the home battery is worth stating, because the symmetry is
tempting. A battery needs terminal value: nothing else stops the receding horizon emptying
it. A car does not — its departure targets already anchor the trajectory, and the window
always sees the next one. Crediting stored charge as well makes it profitable to fill 60 kWh
of car whenever the price dips below the window median.{% endsidenote %}

The commuting schedule is expanded from a pattern: the car leaves at a departure hour and
returns at a return hour on driving days, and the day's energy $$D$$ is spread evenly over
the intervals it is away, so that $$d_k = D / |\mathcal{K}_{\mathrm{away}}|$$ and the state
of charge falls through the day rather than dropping in one step.

### Space heating: heat pump and building

This is the asset that makes the receding horizon earn its keep. A battery stores kWh; a
house stores °C, and it does so for free in mass that is already there.

**Coefficient of performance.** The COP depends only on the ambient temperature, which is
known data — that is what keeps $$q = \mathrm{COP} \cdot p$$ linear and the whole dispatch
model an LP. {% sidenote %}Making it depend on the supply temperature as well, as a real
weather-compensated heat pump does, would make it the product of two decision variables and
cost the linearity.{% endsidenote %} Two models are available:

$$
\mathrm{COP}^{\mathrm{carnot}}(\theta)
= \operatorname{clamp}\!\left(
\frac{\eta_{\mathrm{c}} \,(T_{\mathrm{sup}} + 273.15)}{\max(T_{\mathrm{sup}} - \theta,\; 1)},
\;\; \mathrm{COP}_{\min}, \;\mathrm{COP}_{\max} \right)
$$

$$
\mathrm{COP}^{\mathrm{lin}}(\theta)
= \operatorname{clamp}\!\big( \mathrm{COP}_{\mathrm{ref}} + s\,(\theta - \theta_{\mathrm{ref}}),
\;\; \mathrm{COP}_{\min}, \;\mathrm{COP}_{\max} \big)
$$

With $$\eta_{\mathrm{c}} = 0.45$$ and a 40 °C supply the Carnot form gives about 4.3 at 7 °C
and 3.1 at −5 °C. The _shape_ matters more than the level: it is why a heat pump is
expensive exactly when heat is most needed, and therefore why pre-heating during mild hours
pays.

**Building envelope.** The dwelling is a lumped-capacity RC network in the grey-box
vocabulary of Bacher & Madsen. Three states — indoor air $$T^{\mathrm{i}}$$, envelope mass
$$T^{\mathrm{e}}$$, emitter mass $$T^{\mathrm{h}}$$ — with capacities in kWh/K and
resistances in K/kW, so that a heat flow in kW and a temperature in °C combine without unit
bookkeeping:

$$
\begin{aligned}
C_{\mathrm{i}} \frac{\mathrm{d}T^{\mathrm{i}}}{\mathrm{d}t} &=
\frac{\theta - T^{\mathrm{i}}}{R_{\mathrm{ia}}}
+ \frac{T^{\mathrm{e}} - T^{\mathrm{i}}}{R_{\mathrm{ie}}}
+ \frac{T^{\mathrm{h}} - T^{\mathrm{i}}}{R_{\mathrm{ih}}}
+ \frac{A_{\mathrm{w}} G}{1000}
+ q_{\mathrm{int}} \\[4pt]
C_{\mathrm{e}} \frac{\mathrm{d}T^{\mathrm{e}}}{\mathrm{d}t} &=
\frac{T^{\mathrm{i}} - T^{\mathrm{e}}}{R_{\mathrm{ie}}}
+ \frac{\theta - T^{\mathrm{e}}}{R_{\mathrm{ea}}} \\[4pt]
C_{\mathrm{h}} \frac{\mathrm{d}T^{\mathrm{h}}}{\mathrm{d}t} &=
\frac{T^{\mathrm{i}} - T^{\mathrm{h}}}{R_{\mathrm{ih}}}
+ q_{\mathrm{heat}}
\end{aligned}
$$

$$R_{\mathrm{ia}}$$ is the direct ventilation and infiltration path, which bypasses the
envelope mass and so responds instantly; $$R_{\mathrm{ie}} + R_{\mathrm{ea}}$$ is the path
through it. $$A_{\mathrm{w}}$$ is an effective solar aperture in m², absorbing window area,
orientation, glazing transmittance and shading in one number. The envelope node is what
gives the house slow inertia — without it, pre-heating against tomorrow's prices buys
nothing. The emitter node is what stops heat appearing in the air instantly, which would
overstate how quickly a setback can be recovered.

Writing $$x = [T^{\mathrm{i}}, T^{\mathrm{e}}, T^{\mathrm{h}}]^\top$$ and
$$u = [\theta,\, q_{\mathrm{heat}},\, G,\, q_{\mathrm{int}}]^\top$$, this is
$$\dot{x} = A_{\mathrm{c}} x + B_{\mathrm{c}} u$$. It enters the optimizer in exact
zero-order-hold discrete form, obtained once per simulation by the standard matrix
exponential augmentation:

$$
\begin{bmatrix} A_{\mathrm{d}} & B_{\mathrm{d}} \\ 0 & I \end{bmatrix}
= \exp\!\left( \begin{bmatrix} A_{\mathrm{c}} & B_{\mathrm{c}} \\ 0 & 0 \end{bmatrix} \Delta \right)
$$

{% sidenote %}Exact rather than forward Euler because a 15-minute step is not small against
the emitter time constant of a lightweight radiator; Euler both damps the response and can
go unstable on the fast node.{% endsidenote %}

The dispatch constraints are then plain linear equalities, because $$A_{\mathrm{d}}$$ and
$$B_{\mathrm{d}}$$ are constants and $$q_{\mathrm{heat}}$$ is the only entry of $$u$$ that
is a decision variable:

$$
x_k = A_{\mathrm{d}} x_{k-1} + B_{\mathrm{d}}
\begin{bmatrix} \theta_k \\ \mathrm{COP}(\theta_k)\, p_k \\ G_k \\ q_{\mathrm{int}} \end{bmatrix},
\qquad
0 \leq p_k \leq \overline{P} .
$$

**Comfort.** The optimizer may let the indoor temperature float anywhere inside a band of
half-width $$b$$ around a setpoint series $$s_k$$, and that freedom is the entire
flexibility. The band is enforced _softly_, through non-negative slacks:

$$
T^{\mathrm{i}}_k \geq s_k - b - \xi^{-}_k,
\qquad
T^{\mathrm{i}}_k \leq s_k + b + \xi^{+}_k,
\qquad
\xi^{-}_k, \xi^{+}_k \geq 0
$$

$$
C_{\mathrm{hp}} = \Delta \sum_{k=1}^{n} \big( \kappa^{-} \xi^{-}_k + \kappa^{+} \xi^{+}_k \big),
\qquad \kappa^{-} = 100, \quad \kappa^{+} = 10 \ \ \text{€/K·h}.
$$

Softness is on purpose: an undersized heat pump in a cold snap physically cannot hold the
band, and a model that reports how many degree-hours it fell short is more useful than one
that reports `INFEASIBLE`. The two penalties are deliberately an order of magnitude apart,
because being cold is discomfort while being warmer than a night setback is simply what a
house does as it coasts down. There is **no terminal value term** — the comfort band already
pins the temperature at the end of every window.

**The counterfactual.** Setting the control mode to `:thermostat` fixes $$p_k$$ to what a
hysteresis controller would draw, switching full on below $$s_k - b/2$$ and full off above
$$s_k + b/2$$, seeing only the temperature it currently has. Same building, same heat pump,
no foresight and no price signal — the difference between the two is the value of smart
control.

### Domestic hot water

The tank is the smallest store in the house and the one with the least freedom: a few kWh,
required to be full twice a day at times set by human habit rather than by price. It is
worth modelling anyway because its heat is _expensive_ — reaching 60 °C rather than the
40 °C a radiator needs roughly halves the COP, so every kWh shifted out of the evening peak
is worth about twice what the same kWh is worth to space heating.

With $$c_{\mathrm{w}} = 4.186/3600$$ kWh per litre-kelvin, the usable capacity and the
reserve the household notices are

$$
\overline{E} = V c_{\mathrm{w}} (T_{\mathrm{set}} - T_{\mathrm{in}}),
\qquad
E^{\mathrm{res}} = V c_{\mathrm{w}} (T_{\min} - T_{\mathrm{in}}) .
$$

Tank temperature is affine in stored energy, $$T(E) = T_{\mathrm{in}} + (T_{\mathrm{set}} -
T_{\mathrm{in}}) E / \overline{E}$$, so the standing loss $$U\,(T - T_{\mathrm{amb}})$$ stays
linear in $$E$$. Collecting it into a slope and an offset,

$$
\alpha = \frac{U}{1000} \cdot \frac{T_{\mathrm{set}} - T_{\mathrm{in}}}{\overline{E}},
\qquad
\beta = \frac{U}{1000} \big( T_{\mathrm{in}} - T_{\mathrm{amb}} \big),
$$

the dynamics are

$$
E_k = E_{k-1}
+ \Delta\, \mathrm{COP}(\theta_k)\, p_k
- \big( D_k - \nu_k \big)
- \Delta \big( \alpha E_{k-1} + \beta \big)
$$

$$
0 \leq p_k \leq \overline{P},
\qquad
0 \leq E_k \leq \overline{E},
\qquad
0 \leq \nu_k \leq D_k,
\qquad
E_k \geq E^{\mathrm{res}} - \xi_k, \quad \xi_k \geq 0 .
$$

$$D_k$$ is the hot water drawn in interval $$k$$ (kWh) and $$\nu_k$$ is the part of it the
tank could not supply. Two distinct failure modes are priced separately, and both must be
variables rather than hard constraints or the window becomes infeasible instead of
informative:

$$
C_{\mathrm{dhw}}
= \sum_{k=1}^{n} \big( \kappa^{\mathrm{sf}} \xi_k + \kappa^{\mathrm{us}} \nu_k \big)
\;-\; \frac{\operatorname{median}_k(\pi^{\mathrm{buy}}_k)}{\mathrm{COP}\big(\operatorname{median}_k \theta_k\big)} \, E_n
$$

with $$\kappa^{\mathrm{sf}} = 5$$ and $$\kappa^{\mathrm{us}} = 50$$ €/kWh. The shortfall
$$\xi$$ is water delivered below the minimum temperature — a lukewarm shower. The unserved
$$\nu$$ is water not delivered at all — a cold one. They are not equally bad, hence the
factor of ten. The terminal value is divided by the COP because what is being valued is the
_electricity_ the stored heat displaces, not the heat itself.

The draw profile itself is two Gaussian peaks plus a flat trickle, normalised per day so
that a partial day at the edge of the horizon gets its pro-rata share:

$$
D_k \;\propto\;
\omega \exp\!\left( -\frac{(h_k - h_{\mathrm{m}})^2}{2\sigma_h^2} \right)
+ (1 - \omega) \exp\!\left( -\frac{(h_k - h_{\mathrm{e}})^2}{2\sigma_h^2} \right)
+ 0.02
$$

scaled so each day's total equals
$$V_{\mathrm{day}}\, c_{\mathrm{w}} (T_{\mathrm{set}} - T_{\mathrm{in}})$$.

---

## Exogenous Inputs

### Solar PV

PV production is data to the optimizer, but it is computed rather than assumed. For each
array, from irradiance and sun position to AC power.

**Geometry.** With surface tilt $$\beta$$ and azimuth $$\gamma$$, and solar zenith $$Z$$ and
azimuth $$\gamma_{\mathrm{s}}$$ (all in degrees, 0° = north increasing clockwise), the angle
of incidence is

$$
\cos \theta_{\mathrm{i}} = \cos Z \cos \beta + \sin Z \sin \beta \cos(\gamma_{\mathrm{s}} - \gamma),
$$

evaluated at the **interval midpoint** so a 15-minute average is not biased by the sun's
movement within it. The Kasten & Young relative optical air mass is

$$
m(Z) = \frac{1}{\cos Z + 0.50572\,(96.07995 - Z)^{-1.6364}} .
$$

**Plane-of-array irradiance** is the sum of a beam, a sky-diffuse and a ground-reflected
component:

$$
G^{\mathrm{poa}} = \underbrace{\mathrm{DNI} \cos\theta_{\mathrm{i}}}_{\text{beam}}
\;+\; G^{\mathrm{sky}}
\;+\; \underbrace{\mathrm{GHI} \cdot \rho \cdot \tfrac{1 - \cos\beta}{2}}_{\text{ground}},
$$

with the beam term set to zero when the sun is below the horizon or behind the plane. Three
transposition models are available for $$G^{\mathrm{sky}}$$. Isotropic assumes uniform sky
radiance:

$$
G^{\mathrm{sky}}_{\mathrm{iso}} = \mathrm{DHI} \cdot \frac{1 + \cos\beta}{2}
$$

Hay–Davies splits the diffuse into isotropic and circumsolar parts weighted by the
anisotropy index $$A_{\mathrm{i}} = \operatorname{clamp}(\mathrm{DNI}/\mathrm{DNI}_0, 0, 1)$$:

$$
G^{\mathrm{sky}}_{\mathrm{hd}} = \mathrm{DHI} \left[
A_{\mathrm{i}} R_{\mathrm{b}} + (1 - A_{\mathrm{i}}) \frac{1 + \cos\beta}{2} \right],
\qquad
R_{\mathrm{b}} = \frac{\max(0, \cos\theta_{\mathrm{i}})}{\max(\cos Z, \cos Z_{\min})} .
$$

Perez (1990) adds horizon brightening. With sky clearness $$\epsilon$$ and brightness
$$\Delta_{\mathrm{b}}$$,

$$
\epsilon = \frac{\big(\mathrm{DHI} + \mathrm{DNI}\big)/\mathrm{DHI} + \kappa Z^3}{1 + \kappa Z^3},
\qquad
\Delta_{\mathrm{b}} = \frac{\mathrm{DHI} \cdot m(Z)}{\mathrm{DNI}_0},
\qquad \kappa = 5.535 \times 10^{-6}
$$

$$
F_1 = \max\big(0,\; f_{11} + f_{12}\Delta_{\mathrm{b}} + f_{13} Z_{\mathrm{rad}}\big),
\qquad
F_2 = f_{21} + f_{22}\Delta_{\mathrm{b}} + f_{23} Z_{\mathrm{rad}}
$$

$$
G^{\mathrm{sky}}_{\mathrm{pz}} = \mathrm{DHI} \left[
(1 - F_1)\frac{1 + \cos\beta}{2}
+ F_1 \frac{\max(0, \cos\theta_{\mathrm{i}})}{\max(\cos 85^\circ, \cos Z)}
+ F_2 \sin\beta \right],
$$

with the $$f_{ij}$$ read from the all-sites-composite coefficient table indexed by the
clearness bin. Hay–Davies is the default — nearly as accurate as Perez for annual energy and
far simpler — but Perez is the one to use when tilt or azimuth is itself the quantity under
study.

**From irradiance to power.** Cell temperature follows the NOCT model, and module output is
derated linearly against it:

$$
T_{\mathrm{c}} = \theta + \frac{\mathrm{NOCT} - 20}{800} \, G^{\mathrm{poa}}
$$

$$
P^{\mathrm{dc}} = P_{\mathrm{stc}} \cdot \frac{G^{\mathrm{poa}}}{1000}
\cdot \big( 1 + \alpha_P (T_{\mathrm{c}} - 25) \big) \cdot (1 - \ell)
$$

$$
P^{\mathrm{ac}} = \min\!\big( \max(P^{\mathrm{dc}}, 0)\, \eta_{\mathrm{inv}},\;\; \overline{P}^{\mathrm{ac}} \big)
$$

where $$\ell$$ collects DC-side losses (soiling, mismatch, wiring, degradation) and
$$\alpha_P < 0$$ is the power temperature coefficient. **Each array is clipped at its own
inverter rating before the arrays are summed**, which is why an east/west split can
out-produce a single south array on a small inverter.

For reference shapes — upsampling hourly irradiance to quarter-hours, or generating
synthetic weather — the Haurwitz clear-sky model provides a one-parameter diurnal envelope:

$$
G^{\mathrm{cs}}(Z) = 1098 \cos Z \, \exp\!\left( \frac{-0.059}{\cos Z} \right).
$$

It is used as a _shape_ rather than a prediction: measured irradiance is divided by it to
isolate the effect of cloud, refined on the finer grid, and multiplied back, so its absolute
bias cancels.

### Forecasts

By default the controller optimises against the truth. That is the right default — it
measures what the assets are physically _worth_ — but it is an upper bound, and the gap
between it and a real controller is the value of a forecast.

What the controller believes about a target interval is the truth scaled by an error that
**grows with lead time** and is **correlated in time**:

$$
\widetilde{y}(t) = y(t) \Big( 1 + \sigma \cdot r(\ell) \cdot z(t) \Big),
\qquad
r(\ell) = 1 - \exp\!\left( -\frac{\ell}{h} \right),
$$

where $$\ell$$ is the lead time, $$h$$ the ramp constant, and $$z(t)$$ an
Ornstein–Uhlenbeck-style random walk with correlation timescale $$\tau$$, drawn once for the
whole horizon and indexed by _target_ time. Two properties follow, and both matter.

At zero lead the ramp is zero, so the interval being implemented right now is known exactly
— which is correct, since a controller acting on the current quarter-hour is metering it,
not predicting it. And because $$z$$ is indexed by target rather than by window, a given
interval carries a consistent bias whichever window looks at it.

{% sidenote %}White noise would be the wrong model and would flatter the controller badly:
an optimizer facing independent per-interval errors simply averages them out. Real forecasts
fail by getting _the shape of the day_ wrong — an afternoon forecast sunny turns out cloudy,
and every interval in it is wrong in the same direction at once.{% endsidenote %}

Day-ahead prices are deliberately **not** perturbed. The Dutch auction clears around midday
for every hour of the following day, so prices are known 12 to 36 hours ahead — longer than
the window being optimised. Weather and household load are the genuinely unknown quantities.

---

## Prices, Tariffs and Settlement

### The price signal the controller sees

A Dutch retail contract decomposes into a commodity price $$m_k$$ (day-ahead plus supplier
markup, €/kWh excluding tax), an energy tax $$\tau$$, a variable transport component
$$t^{\mathrm{imp}}_k$$, VAT at rate $$v$$, and a feed-in compensation $$f_k$$. The all-in
price of one imported kWh, and the value of one exported kWh _beyond_ what netting absorbs,
are

$$
\pi^{\mathrm{buy}}_k = \big( m_k + \tau + t^{\mathrm{imp}}_k \big)(1 + v),
\qquad
\pi^{\mathrm{exp}}_k = f_k \cdot v^{\mathrm{fi}} - t^{\mathrm{exp}}_k (1 + v),
$$

where $$v^{\mathrm{fi}}$$ is $$(1+v)$$ if the feed-in rate is paid including VAT and 1
otherwise. The dispatch signal blends the two by the net-metering fraction $$\varphi$$:

$$
\pi^{\mathrm{sell}}_k = \varphi\, \pi^{\mathrm{buy}}_k + (1 - \varphi)\, \pi^{\mathrm{exp}}_k - \varepsilon_\pi .
$$

Under full _salderen_ ($$\varphi = 1$$) an exported kWh really is worth a retail kWh, so a
controller that ignored netting would self-consume when it should not. $$\varphi = 0$$ is
its abolition and intermediate values express a phase-out year — a parameter, not a
hardcoded schedule. $$\varepsilon_\pi = 10^{-4}$$ €/kWh is the degeneracy nudge described
above.

### Settlement

Annual netting is a constraint on the **year**, not on any 48-hour window, so a
receding-horizon objective structurally cannot represent it. The bill is therefore computed
outside the optimizer, from the simulated flows.

With $$E^{\mathrm{imp}} = \Delta \sum_k g^{\mathrm{imp}}_k$$ and
$$E^{\mathrm{exp}} = \Delta \sum_k g^{\mathrm{exp}}_k$$, the netted volume and the netted
share of each exported kWh are

$$
N = \varphi \min\big( E^{\mathrm{imp}},\, E^{\mathrm{exp}} \big),
\qquad
s = \begin{cases} N / E^{\mathrm{exp}} & E^{\mathrm{exp}} > 0 \\ 0 & \text{otherwise.} \end{cases}
$$

The netted share is credited at the commodity price _of the interval it was exported in_;
the remainder is paid at the feed-in rate; energy tax is charged on consumption net of the
netted volume:

$$
\begin{aligned}
C^{\mathrm{com}} &= \Delta \sum_k m_k\, g^{\mathrm{imp}}_k
&\qquad
C^{\mathrm{net}} &= s\, \Delta \sum_k m_k\, g^{\mathrm{exp}}_k \\[3pt]
R^{\mathrm{fi}} &= (1 - s)\, \Delta \sum_k f_k\, g^{\mathrm{exp}}_k
&\qquad
C^{\mathrm{tax}} &= \tau \max\big( 0,\; E^{\mathrm{imp}} - N \big)
\end{aligned}
$$

Fixed items are prorated by $$y = n\Delta / 8760$$ years, so a one-week run is not billed a
full year of standing charges:

$$
C^{\mathrm{tr}} = \Delta \sum_k \big( t^{\mathrm{imp}}_k g^{\mathrm{imp}}_k + t^{\mathrm{exp}}_k g^{\mathrm{exp}}_k \big) + y F^{\mathrm{grid}},
\qquad
C^{\mathrm{fix}} = y \big( S^{\mathrm{sup}} + \mathbb{1}[E^{\mathrm{exp}} > 0]\, F^{\mathrm{fi}} \big).
$$

Collecting the taxable base and applying VAT once gives the bill:

$$
T = C^{\mathrm{com}} - C^{\mathrm{net}} + C^{\mathrm{tax}} - y R^{\mathrm{cred}} + C^{\mathrm{tr}} + C^{\mathrm{fix}}
- \mathbb{1}\big[\text{feed-in incl. VAT}\big] R^{\mathrm{fi}}
$$

$$
B = (1 + v)\, T \;-\; \mathbb{1}\big[\text{feed-in excl. VAT}\big]\, R^{\mathrm{fi}}
$$

where $$R^{\mathrm{cred}}$$ is the annual _vermindering energiebelasting_. The
_capaciteitstarief_ $$F^{\mathrm{grid}}$$ is the term that makes a battery look bad on paper:
it is set by connection size, and no amount of load shifting reduces it, so storage can only
earn against the commodity and tax components.

---

## Investment Metrics

The business case for a configuration is measured against a baseline bill — the same home,
same weather, same prices, no battery. Annualising both and differencing gives the annual
saving $$S = B^{\mathrm{base}}/y - B^{\mathrm{case}}/y$$.

**Effective lifetime.** A battery worked harder wears out sooner, and in a sizing sweep the
small candidates are worked hardest: they cycle more times per kWh installed, because the
surplus they are storing is the same either way. Holding the horizon fixed at the calendar
life would flatter exactly the candidates that need replacing first. With equivalent full
cycles per year

$$
N_{\mathrm{cyc}} = \frac{\Delta \sum_k p^{\mathrm{dis}}_k}{\overline{E} \cdot y},
\qquad\qquad
L = \min\!\left( L_{\mathrm{cal}},\; \frac{N_{\mathrm{rated}}}{N_{\mathrm{cyc}}} \right).
$$

**Cash flows.** Year zero is the capital cost; each later year is the saving, faded by
$$\delta$$ as the battery ages and escalated by $$e$$ as energy prices rise, less operating
cost. A part-year at the end is pro-rated rather than rounded, so a life of 12.99 and one of
13.01 years do not differ by a whole year of savings:

$$
\mathrm{CF}_0 = -C_{\mathrm{capex}},
\qquad
\mathrm{CF}_j = S\,(1 - \delta)^{\,j-1} (1 + e)^{\,j-1} - C_{\mathrm{opex}},
\qquad j = 1, \dots, \lceil L \rceil
$$

with the residual value added in the final year. The headline metrics follow:

$$
\mathrm{NPV} = \sum_{j=0}^{\lceil L \rceil} \frac{\mathrm{CF}_j}{(1 + r)^{\,j}},
\qquad
\mathrm{IRR} : \ \mathrm{NPV}(r^\star) = 0,
\qquad
\mathrm{payback} = \min \Big\{ J : \textstyle\sum_{j \leq J} \mathrm{CF}_j \geq 0 \Big\}
$$

with the payback interpolated within the year in which cumulative cash flow turns positive,
and the IRR reported as undefined when the flows never cross zero — which is the honest
answer for an investment that never pays back.

**Energy metrics.** Two ratios are reported alongside, both attributed _per interval_
because electricity carries no label:

$$
\mathrm{SC} = \frac{\sum_k \min\big( P^{\mathrm{pv}}_k - c_k,\; L_k + \sum_a u_{a,k} \big)}{\sum_k \big( P^{\mathrm{pv}}_k - c_k \big)},
\qquad
\mathrm{SS} = \frac{\sum_k \min\big( L_k,\; P^{\mathrm{pv}}_k - c_k + \sum_a v_{a,k} \big)}{\sum_k L_k} .
$$

{% sidenote %}Comparing total export against total production would not do. Once a battery
can export energy it charged from the grid, export stops being a proxy for un-consumed PV
and the naive ratio can go negative.{% endsidenote %}

### Sizing as a single LP

The sweep above asks "which of these batteries is best". A different question — "how large
would you build it if you could build any size" — can be put directly, by promoting capacity
$$\overline{E}$$ and power $$\overline{P}$$ to continuous decision variables and solving
the whole horizon in one linear program.

Capital cost is annualised with the capital recovery factor

$$
\mathrm{CRF}(r, L) = \frac{r}{1 - (1 + r)^{-L}},
\qquad \mathrm{CRF}(0, L) = \frac{1}{L},
$$

then prorated to the simulated period so it is comparable with that period's energy cost
rather than with a year's:

$$
\min_{\overline{E},\, \overline{P},\, \cdot} \quad
\sum_{k=1}^{n} \Delta \big( \pi^{\mathrm{buy}}_k g^{\mathrm{imp}}_k - \pi^{\mathrm{sell}}_k g^{\mathrm{exp}}_k \big)
\;+\; \Delta\, c_{\mathrm{deg}} \sum_{k=1}^{n} \big( p^{\mathrm{ch}}_k + p^{\mathrm{dis}}_k \big)
\;+\; y \cdot \mathrm{CRF} \cdot \big( \kappa_E \overline{E} + \kappa_P \overline{P} + \kappa_0 \big)
$$

subject to the meter balance, the battery dynamics above, and

$$
p^{\mathrm{ch}}_k \leq \overline{P},
\qquad
p^{\mathrm{dis}}_k \leq \overline{P},
\qquad
\overline{P} \leq \zeta \overline{E},
\qquad
\sigma_{\min} \overline{E} \leq E_k \leq \sigma_{\max} \overline{E},
$$

with one further constraint that does the real work: the horizon is made **cyclic**,

$$
E_1 = E_n + \Delta \left( \eta^{\mathrm{ch}} p^{\mathrm{ch}}_1 - \frac{p^{\mathrm{dis}}_1}{\eta^{\mathrm{dis}}} \right) - \Delta \gamma \overline{E},
$$

so the battery must end where it started and the bound cannot be inflated by selling a full
battery's worth of energy on the last day and never buying it back. The C-rate constraint
$$\overline{P} \leq \zeta \overline{E}$$ matches how batteries are actually built; without
it — and without pricing power through $$\kappa_P$$ — the LP takes power for free and
answers with a tiny, very fast battery that nobody sells.

This is an **upper bound, not an answer**, and the gap between it and a discrete sweep is
the point of having both. It is optimistic in three specific ways: it has perfect foresight
over the entire horizon rather than 48 hours; it minimises the linear dispatch price rather
than the bill, because annual netting couples all 35 040 intervals and cannot be written
into this objective; and it sizes continuously. {% sidenote %}There is also a trap in
comparing the two. `degradation_cost` is a _control-shaping_ parameter: it appears in the
dispatch objective, so this LP is charged for it, but it never appears in a bill, so the
sweep's savings ignore it. Wear is priced in the investment model instead, through lifetime
and capacity fade — charging it twice would be the error.{% endsidenote %}

---

## Simulation Setup
