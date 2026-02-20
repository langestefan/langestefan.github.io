---
layout: distill
title: "Mixed-Integer Home Energy Management with CVXPY + HiGHS in the Browser"
description: "An interactive MIP demo using CVXPY's Disciplined Parameterized Programming (DPP) for battery, EV, and solar PV scheduling with real Dutch day-ahead prices — solved entirely in-browser via Pyodide"
tags: energy optimization pyodide mip
categories: energy
published: false
giscus_comments: true
date: 2026-02-17
featured: true
toc:
  - name: Overview
  - name: Problem Formulation
  - name: Interactive Demo
  - name: How It Works
authors:
  - name: Stefan de Lange
    affiliations:
      name: TU Eindhoven
---

## Overview

A **Home Energy Management System (HEMS)** optimally schedules a household's flexible
assets — home battery, EV charger, and rooftop solar PV — to minimise electricity cost over a
24-hour horizon. The key modelling challenge is that a battery cannot charge and
discharge at the same time, and the grid connection cannot import and export
simultaneously. Enforcing these **mutual-exclusivity** constraints requires **binary
variables**, turning the problem into a **mixed-integer program (MIP)**.

This demo runs **entirely in your browser** — no server, no installation. It uses
[Pyodide](https://pyodide.org/) to run Python +
[CVXPY](https://www.cvxpy.org/) +
[HiGHS](https://highs.dev/) (via SciPy) as WebAssembly.

**Key features:**

- **Disciplined Parameterized Programming (DPP):** the CVXPY model is compiled once;
  subsequent solves (each day, or after changing sliders) just update parameter values
  and re-solve — no expensive re-compilation.
- Real Dutch day-ahead electricity prices at **15-minute resolution**.
- Date picker for multi-day optimisation (rolling 24 h windows).
- Interactive [Plotly](https://plotly.com/javascript/) charts with zoom, pan, and hover.

---
