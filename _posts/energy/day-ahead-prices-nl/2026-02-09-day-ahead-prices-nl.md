---
layout: distill
title: Dutch Day-Ahead Electricity Prices (2019-2026)
description: Interactive visualization of monthly average electricity prices in the Netherlands from 2019 to 2026
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

This analysis visualizes the Dutch day-ahead electricity prices over the years 2019-2026. The data shows the price per kilowatt-hour (kWh) excluding taxes, aggregated by month to reveal pricing trends and patterns.

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

## Data Source

The data used in this analysis comes from Dutch electricity market day-ahead prices,
tracked at 15-minute intervals. The dataset spans from 2019 through early 2026, and can
be downloaded from [jeroen.nl](https://jeroen.nl/dynamische-energie/stroom/prijzen/historisch).
Thanks to Jeroen for making this data publicly available!
