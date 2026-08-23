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

## Management Summary

---

## The Model

### What is a HEMS?

Before we explain how the model is constructed, we need to understand what a HEMS is. If
you are already familiar with the concept, feel free to skip this section.

HEMS stands for Home Energy Management System. It is an abstract term that can mean many
things, which makes it a confusing concept. In this article, we will use the term HEMS
to refer to a system that fulfills our requirements for this study.

A HEMS is a system that has monitoring, control and forecast capabilities and can deploy
these in such a way that they are complimentary functions and new capabilities emerge.
For example, a HEMS can forecast household energy consumption if proper monitoring is in
place. It can then use those forecasts to control assets, considering future demands. A
non-exhaustive list of the capabilities of a HEMS is as follows:

- Monitor both energy consumption and production at the interface to the grid (i.e. the
  electricity meter)
- Can estimate variables that cannot be measured directly, such as the power consumption
  of the household.
- Can _monitor_ and _control_ the most important energy assets in the household. We
  consider here only the "big 4": the battery, the solar PV system, the heat pump and the
  electric vehicle. {% sidenote %}Not every household needs to have all of these assets.
  Control of PV and heat pump is not strictly necessary for optimal operation of the HEMS.
  A HEMS also does not strictly need a battery to be able to control the other assets.
  {% endsidenote %}

The diagram below shows all the pieces of the HEMS and how they interact with each
other. The HEMS is the central piece of the system.

<div class="l-page">
  <figure>{% include_relative hems-block-diagram.svg %}</figure>
</div>

---

## Simulation Setup
