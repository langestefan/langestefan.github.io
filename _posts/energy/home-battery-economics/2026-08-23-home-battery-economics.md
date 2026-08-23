---
layout: distill
title: Home Battery Economics through Simulation
description: What a home battery actually earns back under Dutch dynamic electricity pricing, simulated against real day-ahead prices
tags: energy battery storage economics simulation
categories: energy
giscus_comments: true
date: 2026-08-23
featured: true
published: false
toc:
  - name: Overview
  - name: The Question
  - name: Modelling the Battery
  - name: Simulation Setup
  - name: Results
  - name: Sensitivity
  - name: Conclusion
authors:
  - name: Stefan de Lange
    affiliations:
      name: TU Eindhoven
---

## Overview

<!-- One paragraph: what this post covers and what the reader walks away with. -->

---

## The Question

<!-- Frame the economic question: payback period, arbitrage revenue, self-consumption
     value, and what makes it non-obvious. -->

---

## Modelling the Battery

<!-- The battery model: capacity, charge/discharge limits, round-trip efficiency,
     degradation if modelled. -->

{% comment %}
Embed source ranges from the simulation engine with include_code, e.g.:
{% raw %}{% include_code file="_posts/energy/home-battery-economics/<file>.py" lang="python" start="1" end="20" %}{% endraw %}
NOTE: include_code slices by ABSOLUTE line number - re-check ranges after editing the source.
{% endcomment %}

---

## Simulation Setup

<!-- Price data, time resolution, horizon, tariff components (procurement fee,
     energy tax, VAT, net metering), and the control strategy being simulated. -->

---

## Results

<!-- Charts go here. Two options used elsewhere in this blog:

     1. Pre-rendered Plotly written to assets/plotly/ and embedded as an iframe:
        <div class="l-page">
          <iframe src="{% raw %}{{ '/assets/plotly/<name>.html' | relative_url }}{% endraw %}"
                  frameborder='0' scrolling='no' height="600px" width="100%"></iframe>
        </div>
        Charts must carry the data-theme script so they follow the site's dark mode.

     2. A static image via the standard figure include.
-->

---

## Sensitivity

<!-- How the conclusion moves with battery price, round-trip efficiency,
     price volatility, and tariff assumptions. -->

---

## Conclusion

<!-- The answer to The Question, stated plainly, with its caveats. -->
