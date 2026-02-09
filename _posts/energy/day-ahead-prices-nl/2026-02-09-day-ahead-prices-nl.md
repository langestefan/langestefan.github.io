---
layout: distill
title: Dutch Day-Ahead Electricity Prices (2019-2025)
description: Interactive visualization of monthly average electricity prices in the Netherlands from 2019 to 2025
tags: energy electricity prices visualization
categories: energy
giscus_comments: true
date: 2026-02-09
featured: true
authors:
  - name: Stefan de Lange
    affiliations:
      name: TU Eindhoven
---

## Overview

This analysis visualizes the Dutch day-ahead electricity prices over the years 2019-2025. The data shows the price per kilowatt-hour (kWh) excluding taxes, aggregated by month to reveal pricing trends and patterns.

The visualizations below are interactive - you can hover over bars to see exact values, and switch between different years to compare pricing trends.

---

## Monthly Average Prices by Year

Use the dropdown menu to switch between different years and explore how electricity prices have evolved over time.

<div class="l-page">
  <iframe src="{{ '/assets/plotly/day_ahead_prices_nl.html' | relative_url }}" frameborder='0' scrolling='no' height="600px" width="100%" style="border: 1px dashed grey;"></iframe>
</div>

---

## Year-over-Year Comparison

This chart compares all years side-by-side, making it easy to identify trends and anomalies across the entire period.

<div class="l-page">
  <iframe src="{{ '/assets/plotly/day_ahead_prices_nl_comparison.html' | relative_url }}" frameborder='0' scrolling='no' height="600px" width="100%" style="border: 1px dashed grey;"></iframe>
</div>

---

## Daily Price Spread Analysis - All Years

For consumers with dynamic electricity contracts, understanding price spreads is crucial for optimizing energy usage. This chart shows the potential daily savings per kWh from strategically time-shifting electricity consumption.

**How the spread is calculated:** For each time window (e.g., 8 hours), we calculate the difference between:

- The **average price of the most expensive X hours** in the day, and
- The **average price of the cheapest X hours** in the day

For example, the 8-hour spread shows how much you could save per kWh by shifting your consumption from the 8 most expensive hours to the 8 cheapest hours. This represents the maximum financial benefit from optimally timing your energy usage within that time window—such as running appliances, heating water, or charging batteries during cheaper periods.

All years are overlaid on the same calendar for direct comparison. Use the **Smoothing dropdown** to choose between raw daily data (no smoothing), 7-day rolling average (default), or 30-day rolling average to see different levels of trend detail.

<div class="l-page">
  <iframe src="{{ '/assets/plotly/day_ahead_prices_nl_spread_analysis.html' | relative_url }}" frameborder='0' scrolling='no' height="700px" width="100%" style="border: 1px dashed grey;"></iframe>
</div>

---

## Data Source

The data used in this analysis comes from Dutch electricity market day-ahead prices,
tracked at 15-minute intervals. The dataset spans from 2019 through end of 2025, and can
be downloaded from [jeroen.nl](https://jeroen.nl/dynamische-energie/stroom/prijzen/historisch).
