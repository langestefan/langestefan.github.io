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

This analysis visualizes the Dutch day-ahead electricity prices over the years 2019-2025. The data shows the price per kilowatt-hour (kWh) excluding taxes.

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

## Daily Price Spread Analysis

For consumers with dynamic electricity contracts and or battery systems it can be
interesting to look at the price spread between the most expensive and cheapest hours
within a day. This chart shows the potential daily savings per kWh from strategically time-shifting
electricity consumption.

Use the **Smoothing dropdown** to choose between raw daily data
(no smoothing), 7-day rolling average (default), or 30-day rolling average to see
different levels of trend detail. You can also use the left dropdown to view either the
average of X most expensive or cheapest hours within a day, which can help understand
the price dynamics better.

<div class="l-page">
  <iframe src="{{ '/assets/plotly/day_ahead_prices_nl_spread_analysis.html' | relative_url }}" frameborder='0' scrolling='no' height="700px" width="100%" style="border: 1px dashed grey;"></iframe>
</div>

### How the spread is calculated

For each time window (e.g., 8 hours), we calculate the difference between:

- The **average price of the most expensive X hours** in the day, and
- The **average price of the cheapest X hours** in the day

Or mathematically:

$$
S = \frac{1}{|\mathcal{E}|} \sum_{i \in \mathcal{E}} P_i - \frac{1}{|\mathcal{C}|} \sum_{j \in \mathcal{C}} P_j
$$

Where $\mathcal{E}$ is the set of the X most expensive hours and $\mathcal{C}$ is the
set of the X cheapest hours in a given day. The resulting spread $S$ represents the
potential savings per kWh by shifting consumption from expensive hours to cheap hours
within that time window.

---

## Data Source

The data used in this analysis comes from Dutch electricity market day-ahead prices,
tracked at 15-minute intervals. The dataset spans from 2019 through end of 2025, and can
be downloaded from [jeroen.nl](https://jeroen.nl/dynamische-energie/stroom/prijzen/historisch).
