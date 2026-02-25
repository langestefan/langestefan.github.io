---
layout: distill
title: "Home Energy Management with CVXPY + HiGHS in the Browser"
description: "An interactive HEMS prototyping platform using CVXPY's Disciplined Parameterized Programming (DPP) for battery, EV, and solar PV scheduling with real Dutch day-ahead prices — solved entirely in-browser via Pyodide"
tags: energy optimization pyodide mip
categories: energy
giscus_comments: true
date: 2026-02-17
featured: true
toc:
  - name: Overview
  - name: Interactive Demo
  - name: How It Works
authors:
  - name: Stefan de Lange
    affiliations:
      name: TU Eindhoven
---

A **Home Energy Management System (HEMS)** optimally schedules a household's flexible
assets — home battery, EV charger, and rooftop solar PV — to minimise electricity cost
or maximise self-consumption over a multi-day horizon.

This demo runs **entirely in your browser** — no server, no installation. It uses
[Pyodide](https://pyodide.org/) to run Python +
[CVXPY](https://www.cvxpy.org/) +
[HiGHS](https://highs.dev/) (via SciPy) as WebAssembly.

---

## Interactive Demo

Select a date range, choose your operating mode, configure components, and press
**Run Optimisation**. Each day is solved as a rolling 24 h window with SoC carried
forward.

<!-- Status banner -->
<div id="hems-status" style="
  background: var(--hems-card-bg); border: 1px solid var(--hems-card-border); border-radius: 8px;
  padding: 0.8rem 1.2rem; margin-bottom: 1.5rem; display: flex;
  align-items: center; gap: 0.6rem; font-size: 0.9rem; color: var(--global-text-color);">
  <span id="hems-spinner" style="
    width: 18px; height: 18px; border: 2px solid var(--hems-card-border);
    border-top-color: var(--hems-accent); border-radius: 50%;
    animation: hems-spin 0.8s linear infinite; display: inline-block;">
  </span>
  <span id="hems-status-text">Loading Pyodide runtime…</span>
</div>

<!-- Leaflet.js CSS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
<link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder@2.4.0/dist/Control.Geocoder.css" />

<style>
  @keyframes hems-spin { to { transform: rotate(360deg); } }

  /* ── Theme variables ── */
  :root {
    --hems-green-bg: #f0fdf4; --hems-green-border: #86efac; --hems-green-title: #166534;
    --hems-trade-bg: #eff6ff; --hems-trade-border: #93c5fd; --hems-trade-title: #1e40af;
    --hems-card-bg: #f8fafc; --hems-card-border: #d1d5db;
    --hems-input-bg: #fff; --hems-input-border: #d1d5db; --hems-input-text: #1e293b;
    --hems-label-color: #64748b; --hems-section-title: #334155;
    --hems-accent: #0284c7;
    --hems-mode-text: #1e293b; --hems-mode-em: #334155;
    --hems-mode-li: #1e293b;
  }
  html[data-theme="dark"] {
    --hems-green-bg: rgba(22,101,52,0.18); --hems-green-border: rgba(34,197,94,0.35); --hems-green-title: #4ade80;
    --hems-trade-bg: rgba(30,64,175,0.18); --hems-trade-border: rgba(96,165,250,0.35); --hems-trade-title: #60a5fa;
    --hems-card-bg: rgba(255,255,255,0.04); --hems-card-border: #424246;
    --hems-input-bg: rgba(255,255,255,0.08); --hems-input-border: #555; --hems-input-text: #c9d1d9;
    --hems-label-color: #8b949e; --hems-section-title: #c9d1d9;
    --hems-accent: #58a6ff;
    --hems-mode-text: #e6edf3; --hems-mode-em: #c9d1d9;
    --hems-mode-li: #e6edf3;
  }

  /* ── Operating mode selector buttons ── */
  .hems-mode-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 0.8rem; }
  .hems-mode-btn {
    border-radius: 8px; padding: 0.9rem 1rem; cursor: pointer;
    color: var(--hems-mode-text); transition: all 0.2s;
    text-align: left; position: relative;
  }
  .hems-mode-btn .mode-title { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.25rem; }
  .hems-mode-btn .mode-desc { font-size: 0.82rem; color: var(--hems-mode-em); line-height: 1.35; }
  .hems-mode-btn ul { margin: 0.3rem 0 0; padding-left: 1.1rem; font-size: 0.8rem; color: var(--hems-mode-li); line-height: 1.3; }
  .hems-mode-btn li { margin: 0; padding: 0; }
  .hems-mode-btn.green {
    background: var(--hems-green-bg); border: 2px solid var(--hems-green-border);
  }
  .hems-mode-btn.green .mode-title { color: var(--hems-green-title); }
  .hems-mode-btn.trade {
    background: var(--hems-trade-bg); border: 2px solid var(--hems-trade-border);
  }
  .hems-mode-btn.trade .mode-title { color: var(--hems-trade-title); }
  .hems-mode-btn.selected { box-shadow: 0 0 0 3px var(--hems-accent); }
  .hems-mode-btn:not(.selected) { opacity: 0.55; }
  .hems-mode-btn:hover:not(.selected) { opacity: 0.8; }

  /* ── Controls ── */
  .hems-label { font-size: 0.82rem; color: var(--hems-label-color); font-weight: 500; display: block; margin-bottom: 2px; }
  .hems-label span { color: var(--hems-accent); font-weight: 600; float: right; }
  .hems-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.8rem; margin-bottom: 0.8rem; }
  #hems-controls input[type=range] { width: 100%; accent-color: var(--hems-accent); }
  #hems-controls input[type=date], #hems-controls input[type=number] {
    width: 100%; padding: 4px 6px; border: 1px solid var(--hems-input-border); border-radius: 4px;
    font-size: 0.85rem; background: var(--hems-input-bg); color: var(--hems-input-text);
    -webkit-text-fill-color: var(--hems-input-text);
    color-scheme: light;
  }
  html[data-theme="dark"] #hems-controls input[type=date],
  html[data-theme="dark"] #hems-controls input[type=number] {
    color-scheme: dark;
  }
  #hems-controls input[type=date]::-webkit-datetime-edit,
  #hems-controls input[type=date]::-webkit-datetime-edit-fields-wrapper,
  #hems-controls input[type=date]::-webkit-datetime-edit-text,
  #hems-controls input[type=date]::-webkit-datetime-edit-month-field,
  #hems-controls input[type=date]::-webkit-datetime-edit-day-field,
  #hems-controls input[type=date]::-webkit-datetime-edit-year-field {
    color: var(--hems-input-text);
    -webkit-text-fill-color: var(--hems-input-text);
    opacity: 1;
  }
  #hems-controls input[type=date]::-webkit-calendar-picker-indicator {
    filter: var(--hems-date-icon-filter, none);
    opacity: 0.7; cursor: pointer;
  }
  html[data-theme="dark"] { --hems-date-icon-filter: invert(0.8); }
  #hems-controls select {
    width: 100%; padding: 4px 6px; border: 1px solid var(--hems-input-border); border-radius: 4px;
    font-size: 0.85rem; background: var(--hems-input-bg); color: var(--hems-input-text);
  }
  #hems-run-btn {
    background: var(--hems-accent); color: #fff; border: none; padding: 0.6rem 2rem; border-radius: 6px;
    font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: background 0.2s;
  }
  #hems-run-btn:hover { background: #0369a1; }
  #hems-run-btn:disabled { background: #94a3b8; cursor: not-allowed; }
  .hems-toggle { display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; margin-bottom: 0.3rem; }
  .hems-toggle input[type=checkbox] { accent-color: var(--hems-accent); width: 16px; height: 16px; }
  .hems-section {
    border: 1px solid var(--hems-card-border); border-radius: 6px; padding: 0.8rem; margin-bottom: 0.8rem;
    background: var(--hems-card-bg);
  }
  .hems-section-title {
    font-size: 0.82rem; font-weight: 600; color: var(--hems-section-title); margin-bottom: 0.5rem;
    text-transform: uppercase; letter-spacing: 0.03em;
  }
  .hems-disabled { opacity: 0.35; pointer-events: none; }

  /* ── Collapsible component items ── */
  .hems-comp-list { list-style: none; padding: 0; margin: 0; }
  .hems-comp-item { border: 1px solid var(--hems-card-border); border-radius: 4px; margin-bottom: 0.4rem; }
  .hems-comp-header {
    display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.6rem; cursor: pointer;
    font-size: 0.85rem; font-weight: 500; color: var(--hems-section-title);
    user-select: none; background: transparent; border: none; width: 100%; text-align: left;
  }
  .hems-comp-header:hover { background: rgba(0,0,0,0.03); }
  html[data-theme="dark"] .hems-comp-header:hover { background: rgba(255,255,255,0.04); }
  .hems-comp-header .arrow { transition: transform 0.2s; font-size: 0.7rem; }
  .hems-comp-header.open .arrow { transform: rotate(90deg); }
  .hems-comp-body { padding: 0.4rem 0.6rem 0.6rem; display: none; }
  .hems-comp-body.open { display: block; }
  .hems-add-btn {
    background: none; border: 1px dashed var(--hems-card-border); border-radius: 4px; padding: 0.3rem 0.8rem;
    font-size: 0.82rem; color: var(--hems-accent); cursor: pointer; margin-top: 0.3rem;
  }
  .hems-add-btn:hover { border-color: var(--hems-accent); }
  .hems-remove-btn {
    background: none; border: none; color: #dc2626; cursor: pointer; font-size: 0.8rem; margin-left: auto;
  }

  /* ── Collapsible chart wrappers ── */
  .hems-chart-wrap { margin-bottom: 0.5rem; border: 1px solid var(--hems-card-border); border-radius: 6px; overflow: hidden; }
  .hems-chart-hdr {
    display: flex; align-items: center; gap: 0.45rem; padding: 0.35rem 0.7rem;
    cursor: pointer; user-select: none; font-size: 0.8rem; font-weight: 500;
    color: var(--hems-section-title); background: transparent;
  }
  .hems-chart-hdr:hover { background: rgba(0,0,0,0.03); }
  html[data-theme="dark"] .hems-chart-hdr:hover { background: rgba(255,255,255,0.04); }
  .hems-chart-hdr .arrow { transition: transform 0.2s; font-size: 0.65rem; }
  .hems-chart-hdr.open .arrow { transform: rotate(90deg); }
  .hems-chart-body { display: none; }
  .hems-chart-body.open { display: block; }

  /* ── Location map ── */
  #hems-map { z-index: 0; position: relative; }
  #hems-map .leaflet-control-geocoder { z-index: 1000; }
  #hems-map .leaflet-control-geocoder-alternatives {
    max-height: 200px; overflow-y: auto;
  }
  /* Prevent global blog-theme styles from hiding geocoder results */
  #hems-map .leaflet-control-geocoder-alternatives,
  #hems-map .leaflet-control-geocoder-alternatives li {
    list-style: none !important; display: list-item !important;
    margin: 0 !important; padding: 0 !important;
  }
  #hems-map .leaflet-control-geocoder-alternatives li a {
    display: block; padding: 5px 10px; text-decoration: none;
    color: #333; font-size: 0.82rem; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }
  #hems-map .leaflet-control-geocoder-alternatives li a:hover { background: #f0f0f0; }
  #hems-map .leaflet-control-geocoder input {
    font-size: 0.85rem !important; color: #333 !important;
    background: #fff !important; border: none !important;
    outline: none !important; box-shadow: none !important;
  }
  html[data-theme="dark"] #hems-map { filter: invert(1) hue-rotate(180deg); }
  html[data-theme="dark"] #hems-map .leaflet-control-geocoder { filter: invert(1) hue-rotate(180deg); }
</style>

<!-- Controls -->
<div id="hems-controls" style="margin-bottom:1rem; opacity:0.4; pointer-events:none;">

  <!-- Date & Mode row -->
  <div class="hems-section">
    <div class="hems-section-title">Simulation Settings</div>
    <div class="hems-row">
      <div>
        <label class="hems-label">Start Date</label>
        <input type="date" id="date-start" value="2025-06-01" min="2025-01-01" max="2025-12-25">
      </div>
      <div>
        <label class="hems-label">End Date</label>
        <input type="date" id="date-end" value="2025-06-07" min="2025-01-01" max="2025-12-31">
      </div>
    </div>
    <label class="hems-label">Operating Mode</label>
    <div class="hems-mode-row">
      <div class="hems-mode-btn trade selected" data-mode="trade" onclick="document.querySelectorAll('.hems-mode-btn').forEach(b=>b.classList.remove('selected'));this.classList.add('selected');">
        <div class="mode-title">💰 Trade Mode</div>
        <div class="mode-desc"><em>Cost minimisation with arbitrage.</em></div>
        <ul>
          <li>Sells surplus solar if more profitable</li>
          <li>Battery used for trading</li>
          <li>Charges when beneficial for arbitrage</li>
        </ul>
      </div>
      <div class="hems-mode-btn green" data-mode="green" onclick="document.querySelectorAll('.hems-mode-btn').forEach(b=>b.classList.remove('selected'));this.classList.add('selected');">
        <div class="mode-title">🌳 Green Mode</div>
        <div class="mode-desc"><em>Self-reliance first.</em></div>
        <ul>
          <li>Surplus solar sold only after local use</li>
          <li>Battery reserved for consumption</li>
          <li>Charges when prices are low</li>
        </ul>
      </div>
    </div>
    <div class="hems-row" style="grid-template-columns: 1fr;">
      <div>
        <label class="hems-label">Location (click map or search) <span id="loc-display">Amsterdam (52.377°N, 4.899°E)</span></label>
        <div id="hems-map" style="height: 220px; border-radius: 6px; border: 1px solid var(--hems-input-border);"></div>
      </div>
    </div>
  </div>

  <!-- Supplier / Cost Model -->
  <div class="hems-section">
    <div class="hems-section-title">Cost Model (NL Dynamic Contracts)</div>
    <div class="hems-row">
      <div>
        <label class="hems-label">Supplier Preset</label>
        <select id="supplier-preset">
          <option value="Tibber">Tibber</option>
          <option value="Zonneplan">Zonneplan</option>
          <option value="Frank Energie">Frank Energie</option>
          <option value="custom">Custom</option>
        </select>
      </div>
      <div>
        <label class="hems-label">Procurement Fee (€/kWh) <span id="proc-val">0.0248</span></label>
        <input type="range" id="procurement-fee" min="0" max="0.10" step="0.001" value="0.0248">
      </div>
      <div>
        <label class="hems-label">Sell-back Credit (€/kWh) <span id="sbc-val">0.0000</span></label>
        <input type="range" id="sell-back-credit" min="0" max="0.05" step="0.001" value="0.000">
      </div>
    </div>
    <div class="hems-row">
      <div>
        <label class="hems-label">Energy Tax (€/kWh) <span id="tax-val">0.0916</span></label>
        <input type="range" id="energy-tax" min="0" max="0.20" step="0.001" value="0.0916">
      </div>
      <div>
        <label class="hems-label">VAT (%) <span id="vat-val">21</span></label>
        <input type="range" id="vat-pct" min="0" max="30" step="1" value="21">
      </div>
    </div>
    <div style="margin-top:0.4rem;">
      <label class="hems-toggle"><input type="checkbox" id="net-metering"> <strong>Net Metering</strong></label>
      <span style="font-size:0.78rem; color:var(--hems-label-color); margin-left:0.3rem;">export price = import price (sell-back at full retail rate)</span>
    </div>
  </div>

  <!-- Components -->
  <div class="hems-section">
    <div class="hems-section-title">Components (toggle on/off)</div>

    <!-- Battery -->
    <div style="margin-bottom:0.6rem;">
      <label class="hems-toggle"><input type="checkbox" id="bat-enable" checked> <strong>Home Battery</strong></label>
      <div id="bat-params">
        <div class="hems-row">
          <div>
            <label class="hems-label">Capacity (kWh) <span id="bat-cap-val">13.5</span></label>
            <input type="range" id="bat-cap" min="2" max="30" step="0.5" value="13.5">
          </div>
          <div>
            <label class="hems-label">Max Charge (kW) <span id="bat-pch-val">5.0</span></label>
            <input type="range" id="bat-pch" min="1" max="15" step="0.5" value="5">
          </div>
          <div>
            <label class="hems-label">Max Discharge (kW) <span id="bat-pdis-val">5.0</span></label>
            <input type="range" id="bat-pdis" min="1" max="15" step="0.5" value="5">
          </div>
        </div>
        <div class="hems-row">
          <div>
            <label class="hems-label">Charge Efficiency (%) <span id="bat-ec-val">95</span></label>
            <input type="range" id="bat-ec" min="70" max="100" step="1" value="95">
          </div>
          <div>
            <label class="hems-label">Discharge Efficiency (%) <span id="bat-ed-val">95</span></label>
            <input type="range" id="bat-ed" min="70" max="100" step="1" value="95">
          </div>
          <div>
            <label class="hems-label">Initial SoC (%) <span id="bat-soc0-val">50</span></label>
            <input type="range" id="bat-soc0" min="10" max="100" step="5" value="50">
          </div>
        </div>
      </div>
    </div>

    <!-- EVs (dynamic list) -->
    <div style="margin-bottom:0.6rem;">
      <label class="hems-toggle"><input type="checkbox" id="ev-enable"> <strong>Electric Vehicles</strong></label>
      <div id="ev-section" class="hems-disabled">
        <ul class="hems-comp-list" id="ev-list"></ul>
        <button class="hems-add-btn" id="ev-add-btn" type="button">+ Add EV</button>
      </div>
    </div>

    <!-- Heat Pump -->
    <div style="margin-bottom:0.6rem;">
      <label class="hems-toggle"><input type="checkbox" id="hp-enable"> <strong>Heat Pump</strong></label>
      <div id="hp-params" class="hems-disabled">
        <div class="hems-row">
          <div>
            <label class="hems-label">Supply Temp (°C) <span id="hp-tsupply-val">35</span></label>
            <input type="range" id="hp-tsupply" min="25" max="65" step="1" value="35">
          </div>
          <div>
            <label class="hems-label">Max Thermal Power (kW) <span id="hp-pmax-val">8.0</span></label>
            <input type="range" id="hp-pmax" min="2" max="20" step="0.5" value="8.0">
          </div>
          <div>
            <label class="hems-label">Carnot Efficiency <span id="hp-eta-val">0.45</span></label>
            <input type="range" id="hp-eta" min="0.25" max="0.65" step="0.01" value="0.45">
          </div>
        </div>
        <div class="hems-row">
          <div>
            <label class="hems-label">Heat-loss Coeff H (kW/°C) <span id="hp-h-val">0.20</span></label>
            <input type="range" id="hp-h" min="0.05" max="0.60" step="0.01" value="0.20">
          </div>
          <div>
            <label class="hems-label">Thermal Capacity C (kWh/°C) <span id="hp-c-val">8.0</span></label>
            <input type="range" id="hp-c" min="2" max="20" step="0.5" value="8.0">
          </div>
          <div>
            <label class="hems-label">Set-point Temp (°C) <span id="hp-tset-val">20</span></label>
            <input type="range" id="hp-tset" min="16" max="24" step="0.5" value="20">
          </div>
        </div>
      </div>
    </div>

    <!-- Solar PV (dynamic list) -->
    <div style="margin-bottom:0.6rem;">
      <label class="hems-toggle"><input type="checkbox" id="pv-enable" checked> <strong>Solar PV Arrays</strong></label>
      <div id="pv-section">
        <ul class="hems-comp-list" id="pv-list"></ul>
        <button class="hems-add-btn" id="pv-add-btn" type="button">+ Add Solar Array</button>
      </div>
    </div>

    <!-- Base Load -->
    <div>
      <div class="hems-section-title" style="margin-top:0.4rem;">Base Load</div>
      <div class="hems-row">
        <div>
          <label class="hems-label">Average Consumption (kW) <span id="base-load-val">0.5</span></label>
          <input type="range" id="base-load" min="0.1" max="3.0" step="0.1" value="0.5">
        </div>
      </div>
    </div>

  </div>

  <!-- Run button -->
  <div style="text-align:center; margin-top:1rem;">
    <button id="hems-run-btn" disabled>Run Optimisation</button>
  </div>
</div>

<!-- Results -->
<div id="hems-results-row" style="display:flex; gap:0.7rem; margin-bottom:1rem; flex-wrap:wrap;">
  <div id="hems-results" style="
    flex:1 1 0; min-width:280px;
    background: var(--hems-card-bg); border: 1px solid var(--hems-card-border); border-radius: 8px;
    padding: 1rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; line-height: 1.6; white-space: pre-wrap; min-height: 60px;
    color: var(--global-text-color);">
<span style="color:var(--hems-label-color); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">Output</span>
<span style="color:#059669;">Waiting for Pyodide to load…</span>
  </div>
  <div id="hems-comparison" style="
    flex:1 1 0; min-width:280px;
    background: var(--hems-card-bg); border: 1px solid var(--hems-card-border); border-radius: 8px;
    padding: 1rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; line-height: 1.6; min-height: 60px; overflow:hidden;
    color: var(--global-text-color); display:none;">
  </div>
</div>

<!-- Plot areas — first chart gets the range slider -->
<div class="l-page">
<div id="hems-range-buttons" style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.3rem; flex-wrap:wrap;">
<button id="hems-toggle-charts" onclick="(function(){var ws=document.querySelectorAll('.hems-chart-wrap');var allOpen=Array.from(ws).every(function(w){return w.querySelector('.hems-chart-hdr').classList.contains('open')});ws.forEach(function(w){var h=w.querySelector('.hems-chart-hdr'),b=w.querySelector('.hems-chart-body');if(allOpen){h.classList.remove('open');b.classList.remove('open')}else{h.classList.add('open');b.classList.add('open');var p=b.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p)}});document.getElementById('hems-toggle-charts').textContent=allOpen?'Expand All':'Collapse All'})()" style="margin-left:auto; background:none; border:1px solid var(--hems-card-border); border-radius:4px; padding:0.15rem 0.6rem; font-size:0.72rem; color:var(--hems-accent); cursor:pointer;">Collapse All</button>
</div>
<div id="hems-plot-range" style="margin-bottom:0.5rem;"></div>
<div class="hems-chart-wrap" id="wrap-prices">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var p=this.nextElementSibling.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p);"><span class="arrow">▶</span> Electricity Prices</div>
  <div class="hems-chart-body open"><div id="hems-plot-prices"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-cost">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var p=this.nextElementSibling.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p);"><span class="arrow">▶</span> Cost / Revenue</div>
  <div class="hems-chart-body open"><div id="hems-plot-cost"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-grid">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var p=this.nextElementSibling.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p);"><span class="arrow">▶</span> Net Grid Power</div>
  <div class="hems-chart-body open"><div id="hems-plot-grid"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-power">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var p=this.nextElementSibling.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p);"><span class="arrow">▶</span> Battery Power</div>
  <div class="hems-chart-body open"><div id="hems-plot-power"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-soc">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var p=this.nextElementSibling.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p);"><span class="arrow">▶</span> Battery SoC</div>
  <div class="hems-chart-body open"><div id="hems-plot-soc"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-pv">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var ps=this.nextElementSibling.querySelectorAll('[id^=hems-plot]');ps.forEach(function(p){if(p&&p.data)Plotly.Plots.resize(p)});"><span class="arrow">▶</span> Solar PV Breakdown</div>
  <div class="hems-chart-body open"><div id="hems-plot-pv"></div><div id="hems-plot-pv-curt" style="margin-top:0.3rem;"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-hp">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var ps=this.nextElementSibling.querySelectorAll('[id^=hems-plot]');ps.forEach(function(p){if(p&&p.data)Plotly.Plots.resize(p)});"><span class="arrow">▶</span> Heat Pump</div>
  <div class="hems-chart-body open"><div id="hems-plot-hp"></div><div id="hems-plot-hp-temp" style="margin-top:0.3rem;"></div></div>
</div>
<div class="hems-chart-wrap" id="wrap-ev" style="margin-bottom:1.5rem;">
  <div class="hems-chart-hdr open" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open');var p=this.nextElementSibling.querySelector('[id^=hems-plot]');if(p&&p.data)Plotly.Plots.resize(p);"><span class="arrow">▶</span> EV Breakdown</div>
  <div class="hems-chart-body open"><div id="hems-plot-ev"></div></div>
</div>
</div>

<!-- Leaflet.js -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://unpkg.com/leaflet-control-geocoder@2.4.0/dist/Control.Geocoder.js"></script>

<!-- Plotly.js CDN -->
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>

<!-- Pyodide + HEMS script -->
<script src="https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js"></script>
<script>
(function() {
  "use strict";

  let pyodide = null;
  let solving = false;
  let csvText = null;
  let savedResult = null;  // for scenario comparison
  let pvCounter = 0;
  let evCounter = 0;
  let mapLat = 52.377;
  let mapLon = 4.899;

  // ── Dark-mode aware Plotly colours ──
  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }
  function plotlyColors() {
    const dk = isDark();
    return {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      fontColor: dk ? '#c9d1d9' : '#1e293b',
      gridColor: dk ? '#30363d' : '#e2e8f0',
      zeroColor: dk ? '#484f58' : '#94a3b8',
    };
  }

  // ── Status helpers ──
  function setStatus(msg, ready) {
    document.getElementById('hems-status-text').textContent = msg;
    if (ready) {
      const sp = document.getElementById('hems-spinner');
      if (sp) sp.style.display = 'none';
      const st = document.getElementById('hems-status');
      st.style.borderColor = '#059669';
      st.style.background = 'rgba(5,150,105,0.08)';
      st.style.color = '#059669';
      st.style.fontWeight = '600';
    }
  }

  // ── Supplier presets (no monthly fixed cost) ──
  const SUPPLIERS = {
    "Tibber":        { proc: 0.0248, sbc: 0.0000 },
    "Zonneplan":     { proc: 0.0200, sbc: 0.0200 },
    "Frank Energie": { proc: 0.0182, sbc: 0.0182 },
  };

  // ── Static slider wiring ──
  const sliderMap = [
    { id: 'procurement-fee',  display: 'proc-val',     fmt: v => parseFloat(v).toFixed(4) },
    { id: 'sell-back-credit', display: 'sbc-val',      fmt: v => parseFloat(v).toFixed(4) },
    { id: 'energy-tax',       display: 'tax-val',      fmt: v => parseFloat(v).toFixed(4) },
    { id: 'vat-pct',          display: 'vat-val',      fmt: v => parseInt(v) },
    { id: 'bat-cap',          display: 'bat-cap-val',  fmt: v => parseFloat(v).toFixed(1) },
    { id: 'bat-pch',          display: 'bat-pch-val',  fmt: v => parseFloat(v).toFixed(1) },
    { id: 'bat-pdis',         display: 'bat-pdis-val', fmt: v => parseFloat(v).toFixed(1) },
    { id: 'bat-ec',           display: 'bat-ec-val',   fmt: v => parseInt(v) },
    { id: 'bat-ed',           display: 'bat-ed-val',   fmt: v => parseInt(v) },
    { id: 'bat-soc0',         display: 'bat-soc0-val', fmt: v => parseInt(v) },
    { id: 'hp-tsupply',       display: 'hp-tsupply-val', fmt: v => parseInt(v) },
    { id: 'hp-pmax',          display: 'hp-pmax-val', fmt: v => parseFloat(v).toFixed(1) },
    { id: 'hp-eta',           display: 'hp-eta-val',  fmt: v => parseFloat(v).toFixed(2) },
    { id: 'hp-h',             display: 'hp-h-val',    fmt: v => parseFloat(v).toFixed(2) },
    { id: 'hp-c',             display: 'hp-c-val',    fmt: v => parseFloat(v).toFixed(1) },
    { id: 'hp-tset',          display: 'hp-tset-val', fmt: v => parseFloat(v).toFixed(1) },
    { id: 'base-load',        display: 'base-load-val',fmt: v => parseFloat(v).toFixed(1) },
  ];
  sliderMap.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) el.addEventListener('input', function() {
      document.getElementById(s.display).textContent = s.fmt(this.value);
    });
  });

  // ── Toggle component sections ──
  function wireToggle(checkboxId, paramsId, autoAdd) {
    const cb = document.getElementById(checkboxId);
    const p  = document.getElementById(paramsId);
    if (!cb || !p) return;
    function update() {
      if (cb.checked) {
        p.classList.remove('hems-disabled');
        if (autoAdd) autoAdd();
      } else {
        p.classList.add('hems-disabled');
      }
    }
    cb.addEventListener('change', update);
    update();
  }
  wireToggle('bat-enable', 'bat-params');
  wireToggle('ev-enable', 'ev-section', () => {
    if (document.querySelectorAll('#ev-list .hems-comp-item').length === 0) addEV();
  });
  wireToggle('hp-enable', 'hp-params');
  wireToggle('pv-enable', 'pv-section');

  // ── Supplier preset ──
  document.getElementById('supplier-preset').addEventListener('change', function() {
    const s = SUPPLIERS[this.value];
    if (!s) return;
    document.getElementById('procurement-fee').value = s.proc;
    document.getElementById('proc-val').textContent = s.proc.toFixed(4);
    document.getElementById('sell-back-credit').value = s.sbc;
    document.getElementById('sbc-val').textContent = s.sbc.toFixed(4);
  });

  // ── Location map (Leaflet + Nominatim geocoding) ──
  const hemsMap = L.map('hems-map', { scrollWheelZoom: false }).setView([mapLat, mapLon], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OSM</a>',
    maxZoom: 18,
  }).addTo(hemsMap);
  const mapMarker = L.marker([mapLat, mapLon]).addTo(hemsMap);

  function updateMapLocation(lat, lon, label) {
    mapLat = lat; mapLon = lon;
    mapMarker.setLatLng([lat, lon]);
    hemsMap.setView([lat, lon], hemsMap.getZoom());
    const disp = label || `${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E`;
    document.getElementById('loc-display').textContent = disp;
  }

  const geocoder = L.Control.geocoder({
    collapsed: false,
    defaultMarkText: '',
    placeholder: 'Search city or address…',
    showUniqueResult: false,
    geocoder: L.Control.Geocoder.nominatim({ geocodingQueryParams: { limit: 5 } }),
  }).on('markgeocode', function(e) {
    const { center, name } = e.geocode;
    updateMapLocation(center.lat, center.lng, name);
  }).addTo(hemsMap);

  hemsMap.on('click', function(e) {
    updateMapLocation(e.latlng.lat, e.latlng.lng);
  });

  // ── Dynamic PV list management ──
  function addPV(config) {
    pvCounter++;
    const idx = pvCounter;
    const c = config || { peak: 5.0, eff: 85, curt: false, azimuth: 180, tilt: 35, name: `PV ${idx}` };
    if (!c.name) c.name = `PV ${idx}`;
    const li = document.createElement('li');
    li.className = 'hems-comp-item';
    li.dataset.pvIdx = idx;
    li.innerHTML = `
      <div class="hems-comp-header" onclick="this.classList.toggle('open'); this.nextElementSibling.classList.toggle('open');">
        <span class="arrow">▶</span> <span class="pv-header-name">${c.name}</span>
        <span class="hems-remove-btn" onclick="event.stopPropagation(); this.closest('.hems-comp-item').remove();">✕</span>
      </div>
      <div class="hems-comp-body">
        <div class="hems-row">
          <div>
            <label class="hems-label">Name</label>
            <input type="text" class="pv-name hems-input" value="${c.name}" maxlength="24"
              oninput="this.closest('.hems-comp-item').querySelector('.pv-header-name').textContent=this.value||'Solar'">
          </div>
        </div>
        <div class="hems-row">
          <div>
            <label class="hems-label">Peak Power (kWp) <span class="pv-peak-disp">${c.peak.toFixed(1)}</span></label>
            <input type="range" class="pv-peak" min="0.5" max="20" step="0.5" value="${c.peak}"
              oninput="this.closest('.hems-comp-body').querySelector('.pv-peak-disp').textContent=parseFloat(this.value).toFixed(1)">
          </div>
          <div>
            <label class="hems-label">System Efficiency (%) <span class="pv-eff-disp">${c.eff}</span></label>
            <input type="range" class="pv-eff" min="50" max="100" step="1" value="${c.eff}"
              oninput="this.closest('.hems-comp-body').querySelector('.pv-eff-disp').textContent=parseInt(this.value)">
          </div>
          <div style="display:flex; align-items:end; padding-bottom:4px;">
            <label class="hems-toggle"><input type="checkbox" class="pv-curt" ${c.curt?'checked':''}> Curtailable</label>
          </div>
        </div>
        <div class="hems-row">
          <div>
            <label class="hems-label">Azimuth (°) <span class="pv-az-disp">${c.azimuth}</span></label>
            <input type="range" class="pv-azimuth" min="0" max="360" step="5" value="${c.azimuth}"
              oninput="this.closest('.hems-comp-body').querySelector('.pv-az-disp').textContent=parseInt(this.value)">
            <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:var(--hems-label-color); margin-top:-2px;">
              <span>0° N</span><span>90° E</span><span>180° S</span><span>270° W</span><span>360° N</span>
            </div>
          </div>
          <div>
            <label class="hems-label">Tilt (°) <span class="pv-tilt-disp">${c.tilt}</span></label>
            <input type="range" class="pv-tilt" min="0" max="90" step="1" value="${c.tilt}"
              oninput="this.closest('.hems-comp-body').querySelector('.pv-tilt-disp').textContent=parseInt(this.value)">
            <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:var(--hems-label-color); margin-top:-2px;">
              <span>0° flat</span><span>90° vertical</span>
            </div>
          </div>
        </div>
      </div>`;
    document.getElementById('pv-list').appendChild(li);
  }
  document.getElementById('pv-add-btn').addEventListener('click', () => addPV());

  function getPVConfigs() {
    const items = document.querySelectorAll('#pv-list .hems-comp-item');
    return Array.from(items).map((li, i) => ({
      name:    li.querySelector('.pv-name').value || `PV ${i+1}`,
      peak:    parseFloat(li.querySelector('.pv-peak').value),
      eff:     parseInt(li.querySelector('.pv-eff').value) / 100.0,
      curt:    li.querySelector('.pv-curt').checked,
      azimuth: parseInt(li.querySelector('.pv-azimuth').value),
      tilt:    parseInt(li.querySelector('.pv-tilt').value),
    }));
  }

  // ── Dynamic EV list management ──
  function addEV(config) {
    evCounter++;
    const idx = evCounter;
    const c = config || { cap: 50, pch: 7.0, eff: 90, dep: 32, arr: 72, trip: 10, name: `EV ${idx}` };
    if (!c.name) c.name = `EV ${idx}`;
    const li = document.createElement('li');
    li.className = 'hems-comp-item';
    li.dataset.evIdx = idx;
    li.innerHTML = `
      <div class="hems-comp-header" onclick="this.classList.toggle('open'); this.nextElementSibling.classList.toggle('open');">
        <span class="arrow">▶</span> <span class="ev-header-name">${c.name}</span>
        <span class="hems-remove-btn" onclick="event.stopPropagation(); this.closest('.hems-comp-item').remove();">✕</span>
      </div>
      <div class="hems-comp-body">
        <div class="hems-row">
          <div>
            <label class="hems-label">Name</label>
            <input type="text" class="ev-name hems-input" value="${c.name}" maxlength="24"
              oninput="this.closest('.hems-comp-item').querySelector('.ev-header-name').textContent=this.value||'EV'">
          </div>
        </div>
        <div class="hems-row">
          <div>
            <label class="hems-label">Battery Capacity (kWh) <span class="ev-cap-disp">${c.cap}</span></label>
            <input type="range" class="ev-cap" min="10" max="120" step="5" value="${c.cap}"
              oninput="this.closest('.hems-comp-body').querySelector('.ev-cap-disp').textContent=parseInt(this.value)">
          </div>
          <div>
            <label class="hems-label">Max Charge (kW) <span class="ev-pch-disp">${c.pch.toFixed(1)}</span></label>
            <input type="range" class="ev-pch" min="1" max="22" step="0.5" value="${c.pch}"
              oninput="this.closest('.hems-comp-body').querySelector('.ev-pch-disp').textContent=parseFloat(this.value).toFixed(1)">
          </div>
          <div>
            <label class="hems-label">Charge Efficiency (%) <span class="ev-eff-disp">${c.eff}</span></label>
            <input type="range" class="ev-eff" min="70" max="100" step="1" value="${c.eff}"
              oninput="this.closest('.hems-comp-body').querySelector('.ev-eff-disp').textContent=parseInt(this.value)">
          </div>
        </div>
        <div class="hems-row">
          <div>
            <label class="hems-label">Departure Time <span class="ev-dep-disp">${String(Math.floor(c.dep/4)).padStart(2,'0')}:${String((c.dep%4)*15).padStart(2,'0')}</span></label>
            <input type="range" class="ev-dep" min="0" max="95" step="1" value="${c.dep}"
              oninput="{const v=parseInt(this.value);this.closest('.hems-comp-body').querySelector('.ev-dep-disp').textContent=String(Math.floor(v/4)).padStart(2,'0')+':'+String((v%4)*15).padStart(2,'0')}">
          </div>
          <div>
            <label class="hems-label">Arrival Time <span class="ev-arr-disp">${String(Math.floor(c.arr/4)).padStart(2,'0')}:${String((c.arr%4)*15).padStart(2,'0')}</span></label>
            <input type="range" class="ev-arr" min="0" max="95" step="1" value="${c.arr}"
              oninput="{const v=parseInt(this.value);this.closest('.hems-comp-body').querySelector('.ev-arr-disp').textContent=String(Math.floor(v/4)).padStart(2,'0')+':'+String((v%4)*15).padStart(2,'0')}">
          </div>
          <div>
            <label class="hems-label">Trip Energy (kWh) <span class="ev-trip-disp">${c.trip}</span></label>
            <input type="range" class="ev-trip" min="1" max="60" step="1" value="${c.trip}"
              oninput="this.closest('.hems-comp-body').querySelector('.ev-trip-disp').textContent=parseInt(this.value)">
          </div>
        </div>
      </div>`;
    document.getElementById('ev-list').appendChild(li);
  }
  document.getElementById('ev-add-btn').addEventListener('click', () => addEV());

  function getEVConfigs() {
    const items = document.querySelectorAll('#ev-list .hems-comp-item');
    return Array.from(items).map((li, i) => ({
      name: li.querySelector('.ev-name').value || `EV ${i+1}`,
      cap:  parseFloat(li.querySelector('.ev-cap').value),
      pch:  parseFloat(li.querySelector('.ev-pch').value),
      eff:  parseInt(li.querySelector('.ev-eff').value) / 100.0,
      dep:  parseInt(li.querySelector('.ev-dep').value),
      arr:  parseInt(li.querySelector('.ev-arr').value),
      trip: parseFloat(li.querySelector('.ev-trip').value),
    }));
  }

  // Add default PV array on load (PV is enabled by default)
  addPV({ peak: 5.0, eff: 85, curt: false, azimuth: 90, tilt: 35, name: 'East' });
  addPV({ peak: 5.0, eff: 85, curt: false, azimuth: 270, tilt: 35, name: 'West' });

  // ── Run button ──
  document.getElementById('hems-run-btn').addEventListener('click', solve);

  // ── Fetch weather from Open-Meteo (DNI + DHI for POA irradiance) ──
  async function fetchWeather(startDate, endDate) {
    const lat = mapLat.toFixed(4);
    const lon = mapLon.toFixed(4);
    const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=${startDate}&end_date=${endDate}&hourly=shortwave_radiation,direct_normal_irradiance,diffuse_radiation,temperature_2m,wind_speed_10m&timezone=Europe%2FAmsterdam`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error('Weather API request failed');
    return await resp.json();
  }

  // ── Pyodide init ──
  async function init() {
    try {
      setStatus('Loading Pyodide runtime & price data…');

      const [py, csvResp] = await Promise.all([
        loadPyodide(),
        fetch(new URL('{{ "/assets/data/jeroen_punt_nl_dynamische_stroomprijzen_jaar_2025.csv" | relative_url }}', document.baseURI).href)
      ]);
      pyodide = py;
      csvText = await csvResp.text();

      setStatus('Installing NumPy, SciPy & CVXPY…');
      await pyodide.loadPackage(['numpy', 'scipy', 'cvxpy-base']);

      // ── Write HEMS package to Pyodide filesystem ──
      setStatus('Installing HEMS package…');

      pyodide.FS.mkdir('/home/pyodide/lib');
      pyodide.FS.mkdir('/home/pyodide/lib/HEMS');

      // const.py
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/const.py',
`DT_DEFAULT = 0.25
T_DEFAULT = 24 * int(1 / DT_DEFAULT) - 1
`);

      // __init__.py
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/__init__.py', '');

      // heat_pump.py
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/heat_pump.py',
`import numpy as np
from .base import FixedLoad
from .const import DT_DEFAULT

class HeatPump(FixedLoad):
    """Air-source heat pump as a non-controllable fixed load (1R1C model)."""
    def __init__(self, T_amb, dt=DT_DEFAULT, name="HeatPump",
                 H=0.20, C=8.0, T_set=20.0, T_in_0=20.0,
                 T_supply=35.0, eta_carnot=0.45,
                 cop_min=1.5, cop_max=6.0, P_hp_max=8.0, Q_int=0.7):
        T_amb = np.asarray(T_amb, dtype=float)
        T = len(T_amb)
        self.dt = dt
        self.H = H; self.C = C; self.T_set = T_set
        self.T_supply = T_supply; self.eta_carnot = eta_carnot
        self.cop_min = cop_min; self.cop_max = cop_max
        self.P_hp_max = P_hp_max; self.Q_int = Q_int
        Q_hp, T_in, cop = self._simulate(T_amb, T_in_0)
        self.T_amb = T_amb; self.T_in = T_in
        self.Q_hp = Q_hp; self.cop = cop
        P_el = np.where(cop > 0, Q_hp / cop, 0.0)
        super().__init__(name, P_el)

    def compute_cop(self, T_amb):
        T_amb = np.asarray(T_amb, dtype=float)
        T_h = self.T_supply + 273.15
        T_c = T_amb + 273.15
        dT = np.maximum(T_h - T_c, 1.0)
        cop_carnot = T_h / dT
        cop = self.eta_carnot * cop_carnot
        return np.clip(cop, self.cop_min, self.cop_max)

    def _simulate(self, T_amb, T_in_0):
        T = len(T_amb)
        T_in = np.zeros(T + 1); Q_hp = np.zeros(T)
        T_in[0] = T_in_0
        cop = self.compute_cop(T_amb)
        for t in range(T):
            Q_loss = self.H * (T_in[t] - T_amb[t])
            Q_needed = self.C * (self.T_set - T_in[t]) / self.dt + Q_loss - self.Q_int
            Q_hp[t] = np.clip(Q_needed, 0.0, self.P_hp_max)
            T_in[t + 1] = T_in[t] + self.dt / self.C * (Q_hp[t] + self.Q_int - Q_loss)
        return Q_hp, T_in, cop
`);

      // base.py
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/base.py',
`import cvxpy as cp
import numpy as np
from .const import T_DEFAULT

class GenericLoad:
    def __init__(self, name, T):
        self.name = name
        self.T = T

class FlexibleLoad(GenericLoad):
    def __init__(self, name, T):
        super().__init__(name, T)
        self.P = cp.Variable(T, nonneg=True)

class FixedLoad(GenericLoad):
    def __init__(self, name, power_profile):
        super().__init__(name, len(power_profile))
        self.P = cp.Parameter(self.T, nonneg=True)
        self.P.value = power_profile

class BaseLoad(FixedLoad):
    def __init__(self, name, P_base=0.5):
        if isinstance(P_base, (int, float)):
            power_profile = np.full(T_DEFAULT, P_base)
        else:
            power_profile = np.asarray(P_base, dtype=float)
        super().__init__(name, power_profile)
`);

      // battery.py
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/battery.py',
`import cvxpy as cp
import numpy as np
from .base import FlexibleLoad
from .const import DT_DEFAULT

class Battery(FlexibleLoad):
    def __init__(self, T, dt=DT_DEFAULT, name="Battery",
                 E_max=13.5, P_ch_max=5.0, P_dis_max=5.0,
                 eta_ch=0.95, eta_dis=0.95):
        super().__init__(name, T)
        self.P = cp.Variable(T, name=f"{name}_P_kW")
        self.dt = dt
        self.E_max = E_max
        self.P_ch_max = P_ch_max
        self.P_dis_max = P_dis_max
        self.eta_ch = eta_ch
        self.eta_dis = eta_dis
        self.E = cp.Variable(T + 1, nonneg=True, name=f"{name}_SoC_kWh")
        self.P_ch = cp.Variable(T, nonneg=True, name=f"{name}_P_ch_kW")
        self.P_dis = cp.Variable(T, nonneg=True, name=f"{name}_P_dis_kW")
        if P_dis_max > 0 and P_ch_max > 0:
            self.z = cp.Variable(T, boolean=True, name=f"{name}_Mode")
        else:
            self.z = None
        self.E_0 = cp.Parameter(nonneg=True, name=f"{name}_E0_kWh", value=E_max / 2)
        self.E_T = cp.Parameter(nonneg=True, name=f"{name}_ET_kWh", value=E_max / 2)
        self.E_drain = cp.Parameter(T, nonneg=True, name=f"{name}_drain_kWh")
        self.E_drain.value = np.zeros(T)

    def constraints(self):
        c = []
        c += [self.E[0] == self.E_0]
        c += [self.E[1:] == self.E[:-1]
              + self.dt * (self.eta_ch * self.P_ch - (1.0 / self.eta_dis) * self.P_dis)
              - self.E_drain]
        c += [self.E >= 0, self.E <= self.E_max]
        c += [self.E[self.T] >= self.E_T]
        if self.z is not None:
            c += [self.P_ch <= self.P_ch_max * self.z]
            c += [self.P_dis <= self.P_dis_max * (1 - self.z)]
        else:
            if self.P_ch_max > 0:
                c += [self.P_ch <= self.P_ch_max]
            if self.P_dis_max > 0:
                c += [self.P_dis <= self.P_dis_max]
            else:
                c += [self.P_dis == 0]
        c += [self.P == self.P_ch - self.P_dis]
        return c
`);

      // load.py (EV)
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/load.py',
`import cvxpy as cp
import numpy as np
from .battery import Battery
from .const import DT_DEFAULT

class EV(Battery):
    def __init__(self, T, dt=DT_DEFAULT, name="EV",
                 E_max=50.0, P_ch_max=7.0, P_dis_max=0.0,
                 eta_ch=0.9, eta_dis=0.9):
        super().__init__(T, dt, name, E_max, P_ch_max, P_dis_max, eta_ch, eta_dis)
        self.u = self.E_drain
        self.u.value = np.zeros(T)
        self.a = cp.Parameter(T, nonneg=True, name=f"{name}_Availability")
        self.a.value = np.ones(T)
        self.E_0.value = 20.0
        self.E_T.value = 20.0
        self.schedule_trips()

    def schedule_trips(self, trips=None):
        if trips is None:
            trips = [(8 * 4, 18 * 4, 10.0)]
        self.u.value = np.zeros(self.T)
        self.a.value = np.ones(self.T)
        for dep, arr, energy in trips:
            if 0 <= dep < self.T:
                self.u.value[dep] = energy
                self.a.value[dep:arr] = 0

    def constraints(self):
        c = []
        c += [self.E[0] == self.E_0]
        if self.P_dis_max > 0:
            c += [self.E[1:] == self.E[:-1]
                  + self.dt * (self.eta_ch * self.P_ch - (1.0 / self.eta_dis) * self.P_dis)
                  - self.E_drain]
        else:
            # Simplified SoC for charge-only EV (no P_dis term)
            c += [self.E[1:] == self.E[:-1]
                  + self.dt * self.eta_ch * self.P_ch
                  - self.E_drain]
        c += [self.E >= 0, self.E <= self.E_max]
        c += [self.E[self.T] >= self.E_T]
        if self.P_dis_max > 0 and self.z is not None:
            c += [self.P_ch <= self.P_ch_max * self.z]
            c += [self.P_dis <= self.P_dis_max * (1 - self.z)]
            c += [self.P == self.P_ch - self.P_dis]
        else:
            c += [self.P == self.P_ch]
        # Availability constraints
        c += [self.P_ch <= cp.multiply(self.a, np.full(self.T, self.P_ch_max))]
        if self.P_dis_max > 0:
            c += [self.P_dis <= cp.multiply(self.a, np.full(self.T, self.P_dis_max))]
        return c
`);

      // solar.py (browser-compatible, POA irradiance with tilt/azimuth)
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/solar.py',
`import cvxpy as cp
import numpy as np
from .base import GenericLoad
from .const import DT_DEFAULT

class Solar(GenericLoad):
    def __init__(self, T, dt=DT_DEFAULT, name="Solar", pdc0=5.0, curtailable=False):
        super().__init__(name, T)
        self.dt = dt
        self.pdc0 = pdc0
        self.curtailable = curtailable
        self.P_max = cp.Parameter(T, nonneg=True, name=f"{name}_Pmax_kW")
        self.P_max.value = np.zeros(T)
        if curtailable:
            self.P = cp.Variable(T, nonneg=True, name=f"{name}_P_kW")
        else:
            self.P = cp.Parameter(T, nonneg=True, name=f"{name}_P_kW")
            self.P.value = np.zeros(T)

    @staticmethod
    def compute_poa(dni_wm2, dhi_wm2, tilt_deg, azimuth_deg, latitude_deg, day_of_year, hours):
        """Compute plane-of-array irradiance using isotropic sky model.

        Args:
            dni_wm2: Direct Normal Irradiance array (W/m2)
            dhi_wm2: Diffuse Horizontal Irradiance array (W/m2)
            tilt_deg: Panel tilt from horizontal (0=flat, 90=vertical)
            azimuth_deg: Panel azimuth (0=N, 90=E, 180=S, 270=W)
            latitude_deg: Site latitude in degrees
            day_of_year: Day of year (1-365)
            hours: Array of decimal hours (0.0 to 23.75)

        Returns:
            POA irradiance array (W/m2)
        """
        dni = np.asarray(dni_wm2, dtype=float)
        dhi = np.asarray(dhi_wm2, dtype=float)
        hrs = np.asarray(hours, dtype=float)

        lat_r = np.radians(latitude_deg)
        tilt_r = np.radians(tilt_deg)
        # Convert azimuth from geographic (0=N, 180=S) to solar convention (0=S, +W)
        surf_az_r = np.radians(azimuth_deg - 180.0)

        # Solar declination (Spencer approximation)
        decl = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (day_of_year - 81))))

        # Hour angle (negative=morning, positive=afternoon)
        hour_angle = np.radians(15.0 * (hrs - 12.0))

        # Angle of incidence on tilted surface
        cos_aoi = (np.sin(decl) * np.sin(lat_r) * np.cos(tilt_r)
                 - np.sin(decl) * np.cos(lat_r) * np.sin(tilt_r) * np.cos(surf_az_r)
                 + np.cos(decl) * np.cos(lat_r) * np.cos(tilt_r) * np.cos(hour_angle)
                 + np.cos(decl) * np.sin(lat_r) * np.sin(tilt_r) * np.cos(surf_az_r) * np.cos(hour_angle)
                 + np.cos(decl) * np.sin(tilt_r) * np.sin(surf_az_r) * np.sin(hour_angle))
        cos_aoi = np.maximum(cos_aoi, 0.0)

        # POA = beam component + isotropic diffuse sky
        poa = dni * cos_aoi + dhi * (1.0 + np.cos(tilt_r)) / 2.0
        return np.maximum(poa, 0.0)

    def set_generation(self, ghi_wm2=None, dni_wm2=None, dhi_wm2=None,
                       tilt=0.0, azimuth=180.0, latitude=52.0,
                       day_of_year=1, hours=None, system_eff=0.85):
        """Compute generation from irradiance data.

        If dni and dhi are provided with panel orientation, computes POA
        irradiance. Otherwise falls back to simple GHI model.
        """
        if dni_wm2 is not None and dhi_wm2 is not None and hours is not None:
            poa = self.compute_poa(dni_wm2, dhi_wm2, tilt, azimuth, latitude,
                                   day_of_year, hours)
        elif ghi_wm2 is not None:
            poa = np.asarray(ghi_wm2, dtype=float)
        else:
            poa = np.zeros(self.T)

        pac_kw = np.maximum(self.pdc0 * poa / 1000.0 * system_eff, 0.0)
        self.P_max.value = pac_kw
        if not self.curtailable:
            self.P.value = pac_kw

    def constraints(self):
        if not self.curtailable:
            return []
        return [self.P <= self.P_max]
`);

      // hems.py (no monthly_fixed_cost)
      pyodide.FS.writeFile('/home/pyodide/lib/HEMS/hems.py',
`from __future__ import annotations
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
    COST = "cost"
    SELF_CONSUMPTION = "self_consumption"
    SELF_RELIANCE = "self_reliance"

class HEMS:
    SUPPLIERS = {
        "Tibber":        {"procurement_fee": 0.0248, "sell_back_credit": 0.0000},
        "Zonneplan":     {"procurement_fee": 0.0200, "sell_back_credit": 0.0200},
        "Frank Energie": {"procurement_fee": 0.0182, "sell_back_credit": 0.0182},
    }

    def __init__(self, T=None, dt=DT_DEFAULT,
                 loads=None, pvs=None, evs=None, battery=None,
                 price=None, procurement_fee=0.0, sell_back_credit=0.0,
                 energy_tax=0.0, vat=0.0, net_metering=False,
                 objective="cost", solver=cp.SCIPY):
        self.loads = list(loads) if loads else []
        self.pvs = list(pvs) if pvs else []
        self.evs = list(evs) if evs else []
        self.battery = battery
        self.solver = solver
        self.dt = dt
        self.objective_type = Objective(objective)
        self.procurement_fee = float(procurement_fee)
        self.sell_back_credit = float(sell_back_credit)
        self.energy_tax = float(energy_tax)
        self.vat = float(vat)
        self.net_metering = bool(net_metering)

        all_components = self.loads + self.pvs + self.evs
        if battery is not None:
            all_components.append(battery)

        if T is not None:
            self.T = T
        elif all_components:
            self.T = all_components[0].T
        else:
            raise ValueError("Cannot infer T")

        for comp in all_components:
            if comp.T != self.T:
                raise ValueError(f"Component '{comp.name}' has T={comp.T}, expected {self.T}")

        self.price = cp.Parameter(self.T, name="spot_EUR_kWh")
        if price is not None:
            self.price.value = np.asarray(price, dtype=float)
        else:
            self.price.value = np.zeros(self.T)

        self.P_import = cp.Variable(self.T, nonneg=True, name="P_import_kW")
        self.P_export = cp.Variable(self.T, nonneg=True, name="P_export_kW")

        constraints = []
        P_demand = 0
        for load in self.loads:
            P_demand += load.P
        for ev in self.evs:
            P_demand += ev.P
        if self.battery is not None:
            P_demand += self.battery.P

        P_generation = 0
        for pv in self.pvs:
            P_generation += pv.P

        constraints += [self.P_import - self.P_export == P_demand - P_generation]

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
        obj_expr = self._build_objective()
        self._objective = obj_expr
        self.problem = cp.Problem(obj_expr, constraints)

    def _build_objective(self):
        # Small cycling cost (€/kWh throughput) to prevent degenerate
        # simultaneous / rapid-alternation charge-discharge.
        # Physically represents battery degradation (~0.5 ct/kWh).
        cycle_penalty = 0
        if self.battery is not None:
            cycle_penalty = 0.005 * self.dt * cp.sum(
                self.battery.P_ch + self.battery.P_dis)

        if self.objective_type == Objective.COST:
            vf = 1.0 + self.vat
            import_adder = (self.procurement_fee + self.energy_tax) * vf
            cost_import = self.dt * (
                vf * (self.price @ self.P_import)
                + import_adder * cp.sum(self.P_import)
            )
            if self.net_metering:
                # Net metering: export credited at full import price
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
            pv_total = 0
            for pv in self.pvs:
                pv_total += cp.sum(pv.P)
            return cp.Maximize(
                self.dt * (pv_total - cp.sum(self.P_export)) - cycle_penalty)
        elif self.objective_type == Objective.SELF_RELIANCE:
            return cp.Minimize(
                self.dt * cp.sum(self.P_import) + cycle_penalty)
        else:
            raise ValueError(f"Unknown objective: {self.objective_type}")

    def solve(self, **kwargs):
        kwargs.setdefault("solver", self.solver)
        self.problem.solve(**kwargs)
        if self.problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            raise RuntimeError(f"HEMS failed: status={self.problem.status}")
        imp = self.P_import.value.copy()
        exp = self.P_export.value.copy()
        spot = self.price.value
        if self.objective_type == Objective.COST:
            vf = 1.0 + self.vat
            ia = (self.procurement_fee + self.energy_tax) * vf
            cost_import = float(self.dt * (vf * (spot @ imp) + ia * np.sum(imp)))
            if self.net_metering:
                cost_export = float(self.dt * (vf * (spot @ exp) + ia * np.sum(exp)))
            else:
                cost_export = float(self.dt * (spot @ exp + self.sell_back_credit * np.sum(exp)))
        else:
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

    def step(self):
        if self.battery is not None and self.battery.E.value is not None:
            self.battery.E_0.value = float(self.battery.E.value[-1])
        for ev in self.evs:
            if ev.E.value is not None:
                ev.E_0.value = float(ev.E.value[-1])

    @property
    def total_pv_generation(self):
        total = np.zeros(self.T)
        for pv in self.pvs:
            v = pv.P.value if hasattr(pv.P, "value") else None
            if v is not None:
                total += v
        return total

    @property
    def total_load(self):
        total = np.zeros(self.T)
        for load in self.loads:
            v = load.P.value if hasattr(load.P, "value") else None
            if v is not None:
                total += v
        return total

    @property
    def total_ev_load(self):
        total = np.zeros(self.T)
        for ev in self.evs:
            if ev.P.value is not None:
                total += ev.P.value
        return total
`);

      // Add to sys.path and test import
      setStatus('Building DPP model (one-time compilation)…');
      await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/home/pyodide/lib')
import HEMS
from HEMS.hems import HEMS as HEMSClass, Objective
from HEMS.base import BaseLoad
from HEMS.battery import Battery
from HEMS.load import EV
from HEMS.solar import Solar
import numpy as np

# ── Monkey-patches for 32-bit WASM (Pyodide) ──
# Pyodide runs 32-bit WASM where C long is 32-bit (max 2^31-1).
# Two issues arise:
#   A. CVXPY format_constraints: divmod(product, divisor) where
#      product = A.shape[0]*A.shape[1] > 2^31. If divisor is numpy
#      int64, Python dispatches to numpy __rdivmod__ which calls
#      PyLong_AsLong(product) → OverflowError.
#   B. scipy.milp → _highs_wrapper: sparse matrix indices are int64,
#      HiGHS C code expects C long (32-bit) → OverflowError.
#
# Fix A: patch builtins.divmod to catch OverflowError & retry with int()
import builtins
_py_divmod = builtins.divmod
def _safe_divmod(a, b):
    try:
        return _py_divmod(a, b)
    except OverflowError:
        return _py_divmod(int(a), int(b))
builtins.divmod = _safe_divmod

# Fix B: patch _highs_wrapper to cast int64 indices → int32,
#         and replace milp to also cast before _highs_wrapper.
import scipy.optimize._milp as _mmod
import scipy.optimize as _sopt
_real_hw = _mmod._highs_wrapper
def _safe_hw(c, indptr, indices, data, lhs, rhs, lb, ub, integrality, options):
    return _real_hw(
        c,
        indptr.astype(np.int32) if hasattr(indptr, 'astype') else indptr,
        indices.astype(np.int32) if hasattr(indices, 'astype') else indices,
        data, lhs, rhs, lb, ub, integrality, options)
_mmod._highs_wrapper = _safe_hw

from scipy.optimize._milp import _milp_iv, _highs_to_scipy_status_message
from scipy.optimize import OptimizeResult as _OptResult
def _patched_milp(c, *, integrality=None, bounds=None,
                  constraints=None, options=None):
    args = _milp_iv(c, integrality, bounds, constraints, options)
    c, integ, lb, ub, indptr, indices, data, b_l, b_u, opts = args
    indptr = indptr.astype(np.int32)
    indices = indices.astype(np.int32)
    res_raw = _safe_hw(c, indptr, indices, data, b_l, b_u,
                       lb, ub, integ, opts)
    hs, hm = res_raw.get('status'), res_raw.get('message')
    st, msg = _highs_to_scipy_status_message(hs, hm)
    x = res_raw.get('x')
    return _OptResult(
        status=st, message=msg, success=(st == 0),
        x=np.array(x) if x is not None else None,
        fun=res_raw.get('fun'),
        mip_node_count=res_raw.get('mip_node_count'),
        mip_dual_bound=res_raw.get('mip_dual_bound'),
        mip_gap=res_raw.get('mip_gap'))
_sopt.milp = _patched_milp
_mmod.milp = _patched_milp

_pkg_ok = True
`);

      setStatus('✓ CVXPY + HiGHS + HEMS ready — choose settings and click Run!', true);
      const ctrl = document.getElementById('hems-controls');
      ctrl.style.opacity = '1';
      ctrl.style.pointerEvents = 'auto';
      document.getElementById('hems-run-btn').disabled = false;

    } catch (err) {
      setStatus('Error: ' + err.message);
      console.error(err);
    }
  }

  // ── Comparison helper ──
  function showComparison(current) {
    if (!savedResult) return;
    const comp = document.getElementById('hems-comparison');
    comp.style.display = '';
    const s = savedResult;
    const sModeLbl = s.modeLbl;
    const cModeLbl = current.mode === 'green' ? '🟢 Green' : '🔵 Trade';

    function delta(cur, base, unit, invert) {
      var d = cur - base;
      if (Math.abs(d) < 0.005) return '<span style="color:#6b7280;">=</span>';
      var better = invert ? d < 0 : d > 0;
      var arrow = d > 0 ? '▲' : '▼';
      var color = better ? '#059669' : '#dc2626';
      return '<span style="color:' + color + ';">' + arrow + '&nbsp;' + Math.abs(d).toFixed(unit === '€' ? 2 : 1) + '</span>';
    }

    var sHpKwh = (s.hp_enabled && s.hp_power) ? s.hp_power.reduce(function(a,b){return a+b;},0) * 0.25 : 0;
    var cHpKwh = (current.hp_enabled && current.hp_power) ? current.hp_power.reduce(function(a,b){return a+b;},0) * 0.25 : 0;

    var tcs = 'border-collapse:collapse;width:100%;font-size:0.78rem;table-layout:fixed;';
    var thS = 'text-align:right;padding:0.12rem 0.4rem;font-weight:600;white-space:nowrap;';
    var th0 = 'text-align:left;padding:0.12rem 0.4rem;font-weight:600;white-space:nowrap;';
    var tdR = 'text-align:right;padding:0.12rem 0.4rem;white-space:nowrap;';
    var tdL = 'text-align:left;padding:0.12rem 0.4rem;white-space:nowrap;';
    var sep = '<tr><td colspan="4" style="border-bottom:1px solid var(--hems-card-border);padding:0.15rem 0;"></td></tr>';

    function row(label, bv, cv, dv, bold) {
      var t = bold ? 'font-weight:700;' : '';
      return '<tr><td style="' + tdL + t + '">' + label + '</td><td style="' + tdR + t + '">' + bv + '</td><td style="' + tdR + t + '">' + cv + '</td><td style="' + tdR + t + '">' + dv + '</td></tr>';
    }

    var h = '<span style="color:var(--hems-label-color); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">Comparison vs. Baseline</span>\n';
    h += '<span style="color:#6b7280;font-size:0.78rem;">Baseline: ' + sModeLbl + (s.net_metering ? ' | NM' : '') + '</span>\n';
    h += '<span style="color:#6b7280;font-size:0.78rem;">Current : ' + cModeLbl + (current.net_metering ? ' | NM' : '') + '</span>';
    h += '<table style="' + tcs + '">';
    h += '<colgroup><col style="width:36%"><col style="width:22%"><col style="width:22%"><col style="width:20%"></colgroup>';
    h += '<tr><th style="' + th0 + '"></th><th style="' + thS + '">Base</th><th style="' + thS + '">Current</th><th style="' + thS + '">Delta</th></tr>';
    h += sep;
    h += row('Import kWh', s.import_kwh.toFixed(1), current.import_kwh.toFixed(1), delta(current.import_kwh, s.import_kwh, 'kWh', true));
    h += row('Import €', s.cost_import.toFixed(2), current.cost_import.toFixed(2), delta(current.cost_import, s.cost_import, '€', true));
    h += row('Export kWh', s.export_kwh.toFixed(1), current.export_kwh.toFixed(1), delta(current.export_kwh, s.export_kwh, 'kWh', false));
    h += row('Export €', s.cost_export.toFixed(2), current.cost_export.toFixed(2), delta(current.cost_export, s.cost_export, '€', false));
    if (s.pv_enabled || current.pv_enabled)
      h += row('PV gen kWh', (s.pv_kwh||0).toFixed(1), (current.pv_kwh||0).toFixed(1), delta(current.pv_kwh||0, s.pv_kwh||0, 'kWh', false));
    if (s.hp_enabled || current.hp_enabled)
      h += row('HP elec kWh', sHpKwh.toFixed(1), cHpKwh.toFixed(1), delta(cHpKwh, sHpKwh, 'kWh', true));
    h += row('Demand kWh', s.demand_kwh.toFixed(1), current.demand_kwh.toFixed(1), '<span style="color:#6b7280;">—</span>');
    h += sep;
    h += row('Net cost €', s.net_cost.toFixed(2), current.net_cost.toFixed(2), delta(current.net_cost, s.net_cost, '€', true), true);
    h += '</table>';
    h += '<div style="margin-top:0.5rem;"><button id="hems-clear-comp-btn" style="background:none;border:1px solid var(--hems-card-border);border-radius:4px;padding:0.25rem 0.7rem;font-size:0.75rem;cursor:pointer;color:var(--global-text-color);">Clear Baseline</button></div>';
    comp.innerHTML = h;
    document.getElementById('hems-clear-comp-btn').addEventListener('click', function() {
      savedResult = null;
      comp.style.display = 'none';
      comp.innerHTML = '';
    });
  }

  // ── Solve ──
  async function solve() {
    if (!pyodide || solving) return;
    solving = true;
    const btn     = document.getElementById('hems-run-btn');
    const results = document.getElementById('hems-results');
    btn.disabled  = true;
    results.innerHTML = '<span style="color:var(--hems-label-color); font-size:0.75rem; text-transform:uppercase;">Output</span>\n<span style="color:#0284c7;">Fetching weather data…</span>';

    // ── Read UI values ──
    const startDate = document.getElementById('date-start').value;
    const endDate   = document.getElementById('date-end').value;
    const opMode    = document.querySelector('.hems-mode-btn.selected').dataset.mode;

    const procFee     = parseFloat(document.getElementById('procurement-fee').value);
    const sbc         = parseFloat(document.getElementById('sell-back-credit').value);
    const eTax        = parseFloat(document.getElementById('energy-tax').value);
    const vatPct      = parseInt(document.getElementById('vat-pct').value) / 100.0;
    const netMetering = document.getElementById('net-metering').checked;

    const batEnabled = document.getElementById('bat-enable').checked;
    const batCap   = parseFloat(document.getElementById('bat-cap').value);
    const batPch   = parseFloat(document.getElementById('bat-pch').value);
    const batPdis  = parseFloat(document.getElementById('bat-pdis').value);
    const batEc    = parseInt(document.getElementById('bat-ec').value) / 100.0;
    const batEd    = parseInt(document.getElementById('bat-ed').value) / 100.0;
    const batSoc0  = parseInt(document.getElementById('bat-soc0').value) / 100.0;

    const evEnabled = document.getElementById('ev-enable').checked;
    const evConfigs = evEnabled ? getEVConfigs() : [];

    const pvEnabled = document.getElementById('pv-enable').checked;
    const pvConfigs = pvEnabled ? getPVConfigs() : [];

    const hpEnabled = document.getElementById('hp-enable').checked;
    const hpTsupply = parseFloat(document.getElementById('hp-tsupply').value);
    const hpPmax    = parseFloat(document.getElementById('hp-pmax').value);
    const hpEta     = parseFloat(document.getElementById('hp-eta').value);
    const hpH       = parseFloat(document.getElementById('hp-h').value);
    const hpC       = parseFloat(document.getElementById('hp-c').value);
    const hpTset    = parseFloat(document.getElementById('hp-tset').value);

    const baseLoad = parseFloat(document.getElementById('base-load').value);

    try {
      // ── Fetch weather for PV generation / heat pump ──
      let weatherData = null;
      if ((pvEnabled && pvConfigs.length > 0) || hpEnabled) {
        results.innerHTML = '<span style="color:var(--hems-label-color); font-size:0.75rem; text-transform:uppercase;">Output</span>\n<span style="color:#0284c7;">Fetching weather data from Open-Meteo…</span>';
        weatherData = await fetchWeather(startDate, endDate);
      }

      results.innerHTML = '<span style="color:var(--hems-label-color); font-size:0.75rem; text-transform:uppercase;">Output</span>\n<span style="color:#0284c7;">Parsing data & building HEMS model…</span>';

      // Pass data to Python
      pyodide.globals.set('_csv_text', csvText);
      pyodide.globals.set('_weather_json', weatherData ? JSON.stringify(weatherData) : '');
      pyodide.globals.set('_start_date', startDate);
      pyodide.globals.set('_end_date', endDate);
      pyodide.globals.set('_op_mode', opMode);
      pyodide.globals.set('_proc_fee', procFee);
      pyodide.globals.set('_sbc', sbc);
      pyodide.globals.set('_e_tax', eTax);
      pyodide.globals.set('_vat', vatPct);
      pyodide.globals.set('_net_metering', netMetering);
      pyodide.globals.set('_bat_enabled', batEnabled);
      pyodide.globals.set('_bat_cap', batCap);
      pyodide.globals.set('_bat_pch', batPch);
      pyodide.globals.set('_bat_pdis', batPdis);
      pyodide.globals.set('_bat_ec', batEc);
      pyodide.globals.set('_bat_ed', batEd);
      pyodide.globals.set('_bat_soc0', batSoc0);
      pyodide.globals.set('_ev_configs_json', JSON.stringify(evConfigs));
      pyodide.globals.set('_pv_configs_json', JSON.stringify(pvConfigs));
      pyodide.globals.set('_hp_enabled', hpEnabled);
      pyodide.globals.set('_hp_tsupply', hpTsupply);
      pyodide.globals.set('_hp_pmax', hpPmax);
      pyodide.globals.set('_hp_eta', hpEta);
      pyodide.globals.set('_hp_h', hpH);
      pyodide.globals.set('_hp_c', hpC);
      pyodide.globals.set('_hp_tset', hpTset);
      pyodide.globals.set('_base_load', baseLoad);
      pyodide.globals.set('_latitude', mapLat);
      pyodide.globals.set('_longitude', mapLon);

      const output = await pyodide.runPythonAsync(`
import json, time
import numpy as np
from HEMS.hems import HEMS as HEMSClass, Objective
from HEMS.base import BaseLoad
from HEMS.battery import Battery
from HEMS.load import EV
from HEMS.solar import Solar
from HEMS.heat_pump import HeatPump
import cvxpy as cp

T = 96
dt = 0.25
start_str = str(_start_date)
end_str = str(_end_date)

# ── Parse price CSV ──
lines = _csv_text.strip().split('\\n')
day_prices = {}
for line in lines[1:]:
    parts = line.replace('"','').split(';')
    day = parts[0][:10]
    if start_str <= day <= end_str:
        p = float(parts[2].replace(',','.'))
        day_prices.setdefault(day, []).append(p)

valid_days = sorted(d for d in day_prices if len(day_prices[d]) >= T)
n_days = len(valid_days)

if n_days == 0:
    _result = json.dumps({"status": "error",
        "message": f"No complete days (96 intervals) in range {start_str} to {end_str}."})
else:
    # ── Parse PV and EV configs ──
    pv_configs = json.loads(str(_pv_configs_json))
    ev_configs = json.loads(str(_ev_configs_json))

    # ── Parse weather for PV / HP ──
    hp_enabled = bool(_hp_enabled)
    weather_ghi_hourly = None
    weather_dni_hourly = None
    weather_dhi_hourly = None
    weather_temp_hourly = None
    weather_times_hourly = None
    wj = str(_weather_json)
    if (len(pv_configs) > 0 or hp_enabled) and wj:
        wdata = json.loads(wj)
        weather_ghi_hourly = wdata['hourly']['shortwave_radiation']
        weather_dni_hourly = wdata['hourly'].get('direct_normal_irradiance')
        weather_dhi_hourly = wdata['hourly'].get('diffuse_radiation')
        weather_temp_hourly = wdata['hourly']['temperature_2m']
        weather_times_hourly = wdata['hourly']['time']
    site_lat = float(_latitude)

    # ── Objective mapping ──
    mode = str(_op_mode)
    obj = 'self_reliance' if mode == 'green' else 'cost'

    # ── Build a synthetic demand profile ──
    base_kw = float(_base_load)
    _hours = np.arange(T) * 0.25
    _demand_h = np.array([
        0.30, 0.28, 0.25, 0.25, 0.25, 0.30,
        0.50, 0.80, 1.00, 0.70, 0.55, 0.60,
        0.70, 0.65, 0.55, 0.60, 0.90, 1.30,
        1.50, 1.10, 0.80, 0.60, 0.45, 0.30])
    demand_profile = np.interp(_hours, np.arange(24) + 0.5, _demand_h)
    demand_profile = demand_profile * (base_kw / np.mean(demand_profile))

    # ── Weather helpers ──
    def _extract_day_hourly(hourly_arr, day_str, default=0.0):
        """Extract 24 hourly values for a given day, interpolate to 15-min."""
        if hourly_arr is None:
            return np.full(T, default)
        vals = []
        for i, t in enumerate(weather_times_hourly):
            if t.startswith(day_str):
                vals.append(float(hourly_arr[i]))
        if len(vals) < 24:
            vals = vals + [default] * (24 - len(vals))
        arr = np.array(vals[:24], dtype=float)
        return np.interp(_hours, np.arange(24) + 0.5, arr)

    def get_day_ghi(day_str):
        return np.maximum(_extract_day_hourly(weather_ghi_hourly, day_str, 0.0), 0)

    def get_day_dni(day_str):
        return np.maximum(_extract_day_hourly(weather_dni_hourly, day_str, 0.0), 0)

    def get_day_dhi(day_str):
        return np.maximum(_extract_day_hourly(weather_dhi_hourly, day_str, 0.0), 0)

    def get_day_temp(day_str):
        return _extract_day_hourly(weather_temp_hourly, day_str, 10.0)

    def get_day_of_year(day_str):
        """Compute day-of-year from 'YYYY-MM-DD' string."""
        from datetime import datetime
        return datetime.strptime(day_str, '%Y-%m-%d').timetuple().tm_yday

    # ── Build HEMS components ──
    loads_list = []
    base = BaseLoad("Base", demand_profile)
    loads_list.append(base)

    # Multiple PV arrays
    pvs_list = []
    for pi, pvc in enumerate(pv_configs):
        s = Solar(T, dt, f"Solar_{pi+1}", pdc0=float(pvc['peak']), curtailable=bool(pvc.get('curt', False)))
        doy0 = get_day_of_year(valid_days[0])
        dni0 = get_day_dni(valid_days[0])
        dhi0 = get_day_dhi(valid_days[0])
        s.set_generation(
            dni_wm2=dni0, dhi_wm2=dhi0,
            tilt=float(pvc.get('tilt', 35)),
            azimuth=float(pvc.get('azimuth', 180)),
            latitude=site_lat,
            day_of_year=doy0,
            hours=_hours,
            system_eff=float(pvc['eff']),
        )
        pvs_list.append(s)

    # Battery
    bat = None
    if bool(_bat_enabled):
        bat = Battery(T, dt, "Battery",
                      E_max=float(_bat_cap),
                      P_ch_max=float(_bat_pch),
                      P_dis_max=float(_bat_pdis),
                      eta_ch=float(_bat_ec),
                      eta_dis=float(_bat_ed))
        bat.E_0.value = float(_bat_soc0) * float(_bat_cap)
        bat.E_T.value = float(_bat_soc0) * float(_bat_cap)

    # Multiple EVs
    evs_list = []
    for ei, evc in enumerate(ev_configs):
        ev_obj = EV(T, dt, f"EV_{ei+1}",
                    E_max=float(evc['cap']),
                    P_ch_max=float(evc['pch']),
                    P_dis_max=0.0,
                    eta_ch=float(evc['eff']),
                    eta_dis=float(evc['eff']))
        dep_step = int(evc['dep'])
        arr_step = int(evc['arr'])
        ev_obj.schedule_trips([(dep_step, arr_step, float(evc['trip']))])
        evs_list.append(ev_obj)

    # Heat pump (fixed load, recomputed per day)
    hp = None
    if hp_enabled:
        temp0 = get_day_temp(valid_days[0])
        hp = HeatPump(temp0, dt=dt, name="HeatPump",
                      H=float(_hp_h), C=float(_hp_c),
                      T_set=float(_hp_tset), T_in_0=float(_hp_tset),
                      T_supply=float(_hp_tsupply),
                      eta_carnot=float(_hp_eta),
                      P_hp_max=float(_hp_pmax))
        loads_list.append(hp)

    # ── Create HEMS ──
    hems = HEMSClass(
        T=T, dt=dt,
        loads=loads_list,
        pvs=pvs_list if pvs_list else None,
        evs=evs_list if evs_list else None,
        battery=bat,
        price=np.array(day_prices[valid_days[0]][:T], dtype=float),
        procurement_fee=float(_proc_fee),
        sell_back_credit=float(_sbc),
        energy_tax=float(_e_tax),
        vat=float(_vat),
        net_metering=bool(_net_metering),
        objective=obj,
        solver=cp.SCIPY,
    )

    is_dpp = hems.problem.is_dpp()

    # ── Rolling-horizon solve ──
    all_ts, all_pr = [], []
    all_gi, all_ge, all_net = [], [], []
    all_bat_ch, all_bat_dis, all_bat_soc = [], [], []
    all_ev_ch, all_ev_soc = [], []
    all_pv_gen, all_pv_used, all_pv_curt_arr = [], [], []
    all_demand, all_temp = [], []
    all_imp_price, all_exp_price = [], []

    # Per-unit accumulators (for dedicated per-array / per-EV charts)
    pv_names = [str(pvc.get('name', f'PV {pi+1}')) for pi, pvc in enumerate(pv_configs)]
    ev_names = [str(evc.get('name', f'EV {ei+1}')) for ei, evc in enumerate(ev_configs)]
    per_pv_gen = {name: [] for name in pv_names}   # available generation
    per_pv_used = {name: [] for name in pv_names}  # dispatched / used
    per_ev_ch = {name: [] for name in ev_names}    # charge power
    per_ev_soc = {name: [] for name in ev_names}   # energy / SoC
    per_ev_avail = {name: [] for name in ev_names} # availability (0=away)

    # Heat pump accumulators
    all_hp_power = []    # electrical power [kW]
    all_hp_cop = []      # COP [-]
    all_hp_temp_in = []  # indoor temp [°C]

    total_cost_import = 0.0
    total_cost_export = 0.0
    total_ms = 0.0
    failed = []

    for di_idx, day_str in enumerate(valid_days):
        p = np.array(day_prices[day_str][:T], dtype=float)
        hems.price.value = p

        # Update solar generation for each PV array
        doy = get_day_of_year(day_str)
        for pi, s in enumerate(pvs_list):
            dni = get_day_dni(day_str)
            dhi = get_day_dhi(day_str)
            s.set_generation(
                dni_wm2=dni, dhi_wm2=dhi,
                tilt=float(pv_configs[pi].get('tilt', 35)),
                azimuth=float(pv_configs[pi].get('azimuth', 180)),
                latitude=site_lat,
                day_of_year=doy,
                hours=_hours,
                system_eff=float(pv_configs[pi]['eff']),
            )

        # Update heat pump for today's temperature
        if hp is not None:
            day_temp = get_day_temp(day_str)
            hp_day = HeatPump(day_temp, dt=dt, name="HeatPump",
                              H=float(_hp_h), C=float(_hp_c),
                              T_set=float(_hp_tset), T_in_0=float(_hp_tset),
                              T_supply=float(_hp_tsupply),
                              eta_carnot=float(_hp_eta),
                              P_hp_max=float(_hp_pmax))
            hp.P.value = hp_day.P.value

        if di_idx > 0:
            hems.step()

        t0 = time.time()
        try:
            result = hems.solve(scipy_options={"disp": False, "time_limit": 60.0})
            elapsed = (time.time() - t0) * 1000
            total_ms += elapsed
            total_cost_import += result["cost_import"]
            total_cost_export += result["cost_export"]

            imp = result["P_import"]
            exp = result["P_export"]

            for s in range(T):
                hh = s // 4; mm = (s % 4) * 15
                all_ts.append(f"{day_str}T{hh:02d}:{mm:02d}")
            all_pr.extend(p.tolist())
            all_gi.extend(imp.tolist())
            all_ge.extend(exp.tolist())
            all_net.extend((imp - exp).tolist())
            all_demand.extend(demand_profile.tolist())

            vf = 1.0 + float(_vat)
            imp_pr = (p + float(_proc_fee) + float(_e_tax)) * vf
            exp_pr = imp_pr if bool(_net_metering) else p + float(_sbc)
            all_imp_price.extend(imp_pr.tolist())
            all_exp_price.extend(exp_pr.tolist())

            if bat is not None:
                all_bat_ch.extend(bat.P_ch.value.tolist())
                all_bat_dis.extend(bat.P_dis.value.tolist())
                all_bat_soc.extend(bat.E.value[:T].tolist())
            else:
                z = [0.0] * T
                all_bat_ch.extend(z); all_bat_dis.extend(z); all_bat_soc.extend(z)

            # Aggregate all EVs + per-unit
            ev_ch_day = np.zeros(T)
            ev_soc_day = np.zeros(T)
            for ei, ev_obj in enumerate(evs_list):
                ch_arr = ev_obj.P_ch.value
                soc_arr = ev_obj.E.value[:T]
                ev_ch_day += ch_arr
                ev_soc_day += soc_arr
                per_ev_ch[ev_names[ei]].extend(ch_arr.tolist())
                per_ev_soc[ev_names[ei]].extend(soc_arr.tolist())
                per_ev_avail[ev_names[ei]].extend(ev_obj.a.value.tolist())
            all_ev_ch.extend(ev_ch_day.tolist())
            all_ev_soc.extend(ev_soc_day.tolist())

            # Aggregate all PVs + per-unit
            pv_gen_day = np.zeros(T)
            pv_used_day = np.zeros(T)
            for pi2, s in enumerate(pvs_list):
                gen_arr = s.P_max.value
                if hasattr(s.P, 'value') and s.P.value is not None:
                    pv_val = s.P.value if not isinstance(s.P.value, (int, float)) else np.full(T, s.P.value)
                else:
                    pv_val = s.P_max.value
                pv_gen_day += gen_arr
                pv_used_day += pv_val
                per_pv_gen[pv_names[pi2]].extend(gen_arr.tolist())
                per_pv_used[pv_names[pi2]].extend(pv_val.tolist())
            all_pv_gen.extend(pv_gen_day.tolist())
            all_pv_used.extend(pv_used_day.tolist())
            all_pv_curt_arr.extend((pv_gen_day - pv_used_day).tolist())

            all_temp.extend(get_day_temp(day_str).tolist())

            # Heat pump data
            if hp is not None:
                all_hp_power.extend(hp_day.P.value.tolist())
                all_hp_cop.extend(hp_day.cop.tolist())
                all_hp_temp_in.extend(hp_day.T_in[:T].tolist())
            else:
                z2 = [0.0] * T
                all_hp_power.extend(z2); all_hp_cop.extend(z2); all_hp_temp_in.extend(z2)

        except Exception as e:
            import traceback; traceback.print_exc()
            elapsed = (time.time() - t0) * 1000
            total_ms += elapsed
            failed.append(f"{day_str}: {str(e)}")
            for s in range(T):
                hh = s // 4; mm = (s % 4) * 15
                all_ts.append(f"{day_str}T{hh:02d}:{mm:02d}")
            all_pr.extend(p.tolist())
            z = [0.0] * T
            all_gi.extend(demand_profile.tolist()); all_ge.extend(z)
            all_net.extend(demand_profile.tolist())
            all_bat_ch.extend(z); all_bat_dis.extend(z); all_bat_soc.extend(z)
            all_ev_ch.extend(z); all_ev_soc.extend(z)
            for en in ev_names:
                per_ev_ch[en].extend(z); per_ev_soc[en].extend(z)
                per_ev_avail[en].extend([1.0] * T)
            all_pv_gen.extend(z); all_pv_used.extend(z); all_pv_curt_arr.extend(z)
            for pn in pv_names:
                per_pv_gen[pn].extend(z); per_pv_used[pn].extend(z)
            all_demand.extend(demand_profile.tolist())
            vf = 1.0 + float(_vat)
            imp_pr = (p + float(_proc_fee) + float(_e_tax)) * vf
            exp_pr = p + float(_sbc)
            all_imp_price.extend(imp_pr.tolist())
            all_exp_price.extend(exp_pr.tolist())
            all_temp.extend(get_day_temp(day_str).tolist())
            all_hp_power.extend(z); all_hp_cop.extend(z); all_hp_temp_in.extend(z)

    net_cost = total_cost_import - total_cost_export
    import_kwh = sum(all_gi) * dt
    export_kwh = sum(all_ge) * dt
    pv_kwh = sum(all_pv_used) * dt if all_pv_used else 0
    demand_kwh = sum(all_demand) * dt

    _result = json.dumps({
        "status": "optimal" if len(failed) == 0 else "partial",
        "n_days": n_days,
        "n_failed": len(failed),
        "failed_days": failed,
        "cost_import": total_cost_import,
        "cost_export": total_cost_export,
        "net_cost": net_cost,
        "import_kwh": import_kwh,
        "export_kwh": export_kwh,
        "pv_kwh": pv_kwh,
        "demand_kwh": demand_kwh,
        "solve_ms": total_ms,
        "is_dpp": is_dpp,
        "mode": str(_op_mode),
        "timestamps": all_ts,
        "prices": all_pr,
        "imp_price": all_imp_price,
        "exp_price": all_exp_price,
        "grid_imp": all_gi,
        "grid_exp": all_ge,
        "net_grid": all_net,
        "bat_ch": all_bat_ch,
        "bat_dis": all_bat_dis,
        "bat_soc": all_bat_soc,
        "ev_ch": all_ev_ch,
        "ev_soc": all_ev_soc,
        "pv_gen": all_pv_gen,
        "pv_used": all_pv_used,
        "pv_curt": all_pv_curt_arr,
        "pv_units": [{"name": n, "gen": per_pv_gen[n], "used": per_pv_used[n], "curt": bool(pv_configs[i].get('curt', False))} for i, n in enumerate(pv_names)],
        "ev_units": [{"name": n, "ch": per_ev_ch[n], "soc": per_ev_soc[n], "avail": per_ev_avail[n]} for n in ev_names],
        "demand": all_demand,
        "temp": all_temp,
        "bat_enabled": bool(_bat_enabled),
        "ev_enabled": len(ev_configs) > 0,
        "pv_enabled": len(pv_configs) > 0,
        "bat_cap": float(_bat_cap) if bool(_bat_enabled) else 0,
        "proc_fee": float(_proc_fee),
        "sbc_fee": float(_sbc),
        "e_tax": float(_e_tax),
        "vat_pct": float(_vat),
        "hp_enabled": hp_enabled,
        "hp_power": all_hp_power,
        "hp_cop": all_hp_cop,
        "hp_temp_in": all_hp_temp_in,
        "net_metering": bool(_net_metering),
    })

_result
`);

      const r = JSON.parse(output);

      if (r.status === 'error') {
        results.innerHTML = '<span style="color:#dc2626;">' + r.message + '</span>';
        solving = false; btn.disabled = false;
        return;
      }

      // ── Build results HTML ──
      const modeLbl = r.mode === 'green' ? '🟢 Green (self-reliance)' : '🔵 Trade (min cost)';
      let html = '<span style="color:var(--hems-label-color); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">HEMS Results — ' + modeLbl + '</span>\n';
      html += '<span style="color:#059669;">Days: ' + r.n_days + (r.n_failed > 0 ? ' (' + r.n_failed + ' failed)' : ' ✓') + '  |  DPP: ' + (r.is_dpp ? '✓' : '✗') + '  |  Solve: ' + r.solve_ms.toFixed(0) + ' ms</span>\n';
      if (r.net_metering) html += '<span style="color:#d97706;">Net metering: ON</span>\n';
      html += '─────────────────────────────────\n';
      html += 'Import       : ' + r.import_kwh.toFixed(1) + ' kWh  (€ ' + r.cost_import.toFixed(2) + ')\n';
      html += 'Export       : ' + r.export_kwh.toFixed(1) + ' kWh  (€ ' + r.cost_export.toFixed(2) + ')\n';
      if (r.pv_enabled) html += 'PV generated : ' + r.pv_kwh.toFixed(1) + ' kWh\n';
      if (r.hp_enabled) { var hpKwh = r.hp_power.reduce((a,b) => a+b, 0) * 0.25; html += 'Heat pump    : ' + hpKwh.toFixed(1) + ' kWh (elec)\n'; }
      html += 'Demand       : ' + r.demand_kwh.toFixed(1) + ' kWh\n';
      html += '─────────────────────────────────\n';
      html += '<strong>Net cost     : € ' + r.net_cost.toFixed(2) + '</strong>\n';
      if (r.n_failed > 0) {
        html += '<span style="color:#dc2626;">Failed: ' + r.failed_days.join(', ') + '</span>\n';
      }
      html += '\n<button id="hems-save-btn" style="background:var(--hems-accent);color:#fff;border:none;border-radius:4px;padding:0.25rem 0.7rem;font-size:0.75rem;cursor:pointer;">Save as Baseline</button>';
      results.innerHTML = html;

      // Wire save button
      document.getElementById('hems-save-btn').addEventListener('click', function() {
        savedResult = {
          mode: r.mode,
          modeLbl: modeLbl,
          n_days: r.n_days,
          import_kwh: r.import_kwh,
          export_kwh: r.export_kwh,
          cost_import: r.cost_import,
          cost_export: r.cost_export,
          pv_kwh: r.pv_kwh,
          pv_enabled: r.pv_enabled,
          hp_enabled: r.hp_enabled,
          hp_power: r.hp_power,
          demand_kwh: r.demand_kwh,
          net_cost: r.net_cost,
          solve_ms: r.solve_ms,
          net_metering: r.net_metering,
        };
        showComparison(r);
      });

      // Show comparison if baseline exists
      if (savedResult) showComparison(r);

      // ── Plotly Charts ──
      plotCharts(r);

    } catch (err) {
      results.innerHTML = '<span style="color:#dc2626;">Error: ' + err.message + '</span>\n' + err.stack;
      console.error(err);
    }
    solving = false;
    btn.disabled = false;
  }

  // ── Plotting (dark-mode aware, shared range slider) ──
  const PLOT_IDS = ['hems-plot-range', 'hems-plot-prices', 'hems-plot-cost', 'hems-plot-grid', 'hems-plot-power', 'hems-plot-soc', 'hems-plot-pv', 'hems-plot-pv-curt', 'hems-plot-hp', 'hems-plot-hp-temp', 'hems-plot-ev'];
  let syncingRange = false; // prevent infinite loops

  function plotCharts(r) {
    const ts = r.timestamps;
    const c = plotlyColors();

    const layoutBase = {
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: c.fontColor },
      paper_bgcolor: c.paper_bgcolor,
      plot_bgcolor: c.plot_bgcolor,
      margin: { l: 60, r: 60, t: 40, b: 30 },
      legend: { orientation: 'h', y: -0.18, x: 0.5, xanchor: 'center' },
      hovermode: 'x unified',
    };
    const gridAxis = { gridcolor: c.gridColor, zerolinecolor: c.zeroColor };
    const plotCfg = { responsive: true, displayModeBar: true,
      modeBarButtonsToRemove: ['lasso2d','select2d','autoScale2d'] };

    // 0. Date-Range Selector — rangeslider with HTML preset buttons
    // Build HTML quick-select buttons
    const nDays = r.n_days || 1;
    const btnContainer = document.getElementById('hems-range-buttons');
    let btnHtml = '';
    const btnPresets = [];
    if (nDays > 1) btnPresets.push({ label: '1 day', days: 1 });
    if (nDays > 3) btnPresets.push({ label: '3 days', days: 3 });
    if (nDays > 7) btnPresets.push({ label: '1 week', days: 7 });
    btnPresets.push({ label: 'All', days: 0 });
    btnPresets.forEach(p => {
      btnHtml += ' <button class="hems-range-btn" data-days="' + p.days + '" style="'
        + 'font-size:0.7rem; padding:2px 10px; border:1px solid var(--hems-border-color);'
        + 'border-radius:4px; background:var(--hems-card-bg); color:var(--hems-text-color);'
        + 'cursor:pointer;">' + p.label + '</button>';
    });
    btnContainer.innerHTML = btnHtml;

    // Wire up HTML buttons
    btnContainer.querySelectorAll('.hems-range-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        const days = parseInt(this.dataset.days);
        const rangeDiv = document.getElementById('hems-plot-range');
        if (days === 0) {
          Plotly.relayout(rangeDiv, { 'xaxis.autorange': true });
        } else {
          // Show last N days from the end of the data
          const last = ts[ts.length - 1];
          const end = new Date(last);
          const start = new Date(end.getTime() - days * 86400000);
          Plotly.relayout(rangeDiv, {
            'xaxis.range[0]': start.toISOString(),
            'xaxis.range[1]': end.toISOString()
          });
        }
      });
    });

    // The range chart: a visible sparkline PLUS a full-width rangeslider underneath
    Plotly.newPlot('hems-plot-range', [
      { x: ts, y: r.imp_price, type: 'scatter', mode: 'lines', name: 'Price',
        line: { color: 'rgba(220,38,38,0.5)', width: 1 },
        fill: 'tozeroy', fillcolor: 'rgba(220,38,38,0.08)',
        hoverinfo: 'x', showlegend: false },
    ], {
      font: { family: 'Inter, system-ui, sans-serif', size: 10, color: c.fontColor },
      paper_bgcolor: c.paper_bgcolor,
      plot_bgcolor: c.plot_bgcolor,
      margin: { l: 60, r: 60, t: 4, b: 30 },
      xaxis: {
        ...gridAxis, type: 'date',
        rangeslider: {
          visible: true,
          thickness: 0.35,
          bgcolor: c.paper_bgcolor,
          bordercolor: c.gridColor,
          borderwidth: 1,
        },
        showticklabels: true,
        tickformat: '%b %d',
        tickfont: { size: 9 },
      },
      yaxis: { visible: false, fixedrange: true },
      hovermode: 'x',
      height: 120,
    }, { responsive: true, displayModeBar: false });

    // 1. Electricity Prices
    Plotly.newPlot('hems-plot-prices', [
      { x: ts, y: r.imp_price, type: 'scatter', mode: 'lines', name: 'Import Price',
        line: { color: '#dc2626', width: 1.2 }, fill: 'tozeroy', fillcolor: 'rgba(220,38,38,0.08)' },
      { x: ts, y: r.exp_price, type: 'scatter', mode: 'lines', name: 'Export Price',
        line: { color: '#059669', width: 1.2, dash: 'dot' } },
    ], {
      ...layoutBase,
      xaxis: { ...gridAxis, type: 'date' },
      yaxis: { title: 'Price (€/kWh)', ...gridAxis, side: 'left' },
      height: 300,
    }, plotCfg);

    // 1a. Cost / Revenue per timestep
    const dt = 0.25;
    const costPerStep = r.grid_imp.map((imp, i) => imp * r.imp_price[i] * dt - r.grid_exp[i] * r.exp_price[i] * dt);
    // Cumulative cost
    const cumCost = [];
    costPerStep.reduce((acc, v, i) => { cumCost.push(acc + v); return acc + v; }, 0);
    Plotly.newPlot('hems-plot-cost', [
      { x: ts, y: costPerStep, type: 'bar', name: 'Net Cost',
        marker: { color: costPerStep.map(v => v >= 0 ? 'rgba(220,38,38,0.55)' : 'rgba(5,150,105,0.55)') } },
      { x: ts, y: cumCost, type: 'scatter', mode: 'lines', name: 'Cumulative',
        yaxis: 'y2', line: { color: '#6366f1', width: 2 } },
    ], {
      ...layoutBase,
      xaxis: { ...gridAxis, type: 'date' },
      yaxis: { title: 'Cost (€)', ...gridAxis, zeroline: true, zerolinecolor: c.zeroColor },
      yaxis2: { title: 'Cumulative (€)', overlaying: 'y', side: 'right', ...gridAxis },
      height: 300,
    }, plotCfg);

    // 1b. Net Grid Flow
    Plotly.newPlot('hems-plot-grid', [
      { x: ts, y: r.net_grid, type: 'bar', name: 'Net Grid',
        marker: { color: r.net_grid.map(v => v >= 0 ? 'rgba(220,38,38,0.6)' : 'rgba(5,150,105,0.6)') } },
      { x: ts, y: r.grid_imp, type: 'scatter', mode: 'lines', name: 'Import',
        line: { color: '#dc2626', width: 1, dash: 'dot' } },
      { x: ts, y: r.grid_exp.map(v => -v), type: 'scatter', mode: 'lines', name: 'Export',
        line: { color: '#059669', width: 1, dash: 'dot' } },
    ], {
      ...layoutBase,
      xaxis: { ...gridAxis, type: 'date' },
      yaxis: { title: 'Power (kW)', ...gridAxis, zeroline: true, zerolinecolor: c.zeroColor },
      height: 300,
    }, plotCfg);

    // Per-unit color palette
    const unitPalette = ['#a855f7', '#06b6d4', '#f97316', '#ec4899', '#84cc16', '#6366f1', '#14b8a6', '#e11d48'];

    // 2. Battery Power Schedule
    const traces2 = [];
    if (r.bat_enabled) {
      traces2.push({ x: ts, y: r.bat_ch, type: 'bar', name: 'Charge',
        marker: { color: '#22c55e' }, opacity: 0.7 });
      traces2.push({ x: ts, y: r.bat_dis.map(d => -d), type: 'bar', name: 'Discharge',
        marker: { color: '#ef4444' }, opacity: 0.7 });
    }
    traces2.push({ x: ts, y: r.demand, type: 'scatter', mode: 'lines', name: 'Base Load',
      line: { color: '#64748b', width: 1.5, dash: 'dash' } });
    if (r.hp_enabled) {
      traces2.push({ x: ts, y: r.hp_power, type: 'scatter', mode: 'lines', name: 'Heat Pump',
        line: { color: '#e11d48', width: 1.5, dash: 'dot' } });
    }

    if (r.bat_enabled) {
      Plotly.newPlot('hems-plot-power', traces2, {
        ...layoutBase,
        xaxis: { ...gridAxis, type: 'date' },
        yaxis: { title: 'Power (kW)', ...gridAxis, zeroline: true, zerolinecolor: c.zeroColor },
        barmode: 'relative',
        height: 320,
      }, plotCfg);
    } else {
      Plotly.purge('hems-plot-power');
      document.getElementById('hems-plot-power').innerHTML = '';
    }

    // 3. Battery State of Charge
    if (r.bat_enabled) {
      Plotly.newPlot('hems-plot-soc', [
        { x: ts, y: r.bat_soc, type: 'scatter', mode: 'lines', name: 'Battery SoC',
          fill: 'tozeroy', line: { color: '#0284c7', width: 2 }, fillcolor: 'rgba(2,132,199,0.12)' },
      ], {
        ...layoutBase,
        xaxis: { ...gridAxis, type: 'date' },
        yaxis: { title: 'SoC (kWh)', ...gridAxis, rangemode: 'tozero' },
        height: 300,
      }, plotCfg);
    } else {
      Plotly.purge('hems-plot-soc');
      document.getElementById('hems-plot-soc').innerHTML = '';
    }

    // 4. Solar PV Breakdown (per-array)
    if (r.pv_enabled && r.pv_units) {
      const pvColors = ['#f59e0b', '#ea580c', '#d97706', '#c2410c', '#b45309', '#9a3412'];
      const traces4 = [];
      r.pv_units.forEach((pv, i) => {
        const col = pvColors[i % pvColors.length];
        traces4.push({ x: ts, y: pv.used, type: 'bar', name: pv.name,
          marker: { color: col }, opacity: 0.7 });
      });
      // Total used as dashed line (sum of used, excludes curtailed)
      const totalUsed = r.pv_units[0].used.map((_, j) => r.pv_units.reduce((s, pv) => s + pv.used[j], 0));
      traces4.push({ x: ts, y: totalUsed, type: 'scatter', mode: 'lines', name: 'Total',
        line: { color: '#f97316', width: 1.5, dash: 'dash' } });

      Plotly.newPlot('hems-plot-pv', traces4, {
        ...layoutBase,
        xaxis: { ...gridAxis, type: 'date' },
        yaxis: { title: 'Power (kW)', ...gridAxis, rangemode: 'tozero' },
        barmode: 'stack',
        height: 320,
      }, plotCfg);

      // Curtailment sub-chart (only if any array is curtailable)
      const anyCurt = r.pv_units.some(pv => pv.curt);
      if (anyCurt) {
        const curtTraces = [];
        r.pv_units.forEach((pv, i) => {
          if (!pv.curt) return;
          const col = pvColors[i % pvColors.length];
          const curt = pv.gen.map((g, j) => Math.max(0, g - pv.used[j]));
          curtTraces.push({ x: ts, y: curt, type: 'bar', name: pv.name,
            marker: { color: col }, opacity: 0.5 });
        });
        Plotly.newPlot('hems-plot-pv-curt', curtTraces, {
          ...layoutBase,
          margin: { ...layoutBase.margin, b: 50 },
          showlegend: true,
          xaxis: { ...gridAxis, type: 'date' },
          yaxis: { title: 'Curtailed (kW)', ...gridAxis, rangemode: 'tozero' },
          barmode: 'stack',
          height: 240,
        }, plotCfg);
      } else {
        Plotly.purge('hems-plot-pv-curt');
        document.getElementById('hems-plot-pv-curt').innerHTML = '';
      }
    } else {
      Plotly.purge('hems-plot-pv');
      document.getElementById('hems-plot-pv').innerHTML = '';
      Plotly.purge('hems-plot-pv-curt');
      document.getElementById('hems-plot-pv-curt').innerHTML = '';
    }

    // 5b. Heat Pump charts (electrical power + COP, indoor/outdoor temperature)
    if (r.hp_enabled) {
      // Electrical power + COP on secondary y-axis
      Plotly.newPlot('hems-plot-hp', [
        { x: ts, y: r.hp_power, type: 'scatter', mode: 'lines', name: 'Elec. Power',
          fill: 'tozeroy', line: { color: '#e11d48', width: 1.5 }, fillcolor: 'rgba(225,29,72,0.12)' },
        { x: ts, y: r.hp_cop, type: 'scatter', mode: 'lines', name: 'COP',
          yaxis: 'y2', line: { color: '#8b5cf6', width: 1.5, dash: 'dot' } },
      ], {
        ...layoutBase,
        xaxis: { ...gridAxis, type: 'date' },
        yaxis: { title: 'Elec. Power (kW)', ...gridAxis, rangemode: 'tozero' },
        yaxis2: { title: 'COP', overlaying: 'y', side: 'right', ...gridAxis, rangemode: 'tozero' },
        height: 280,
      }, plotCfg);

      // Temperature chart
      Plotly.newPlot('hems-plot-hp-temp', [
        { x: ts, y: r.temp, type: 'scatter', mode: 'lines', name: 'Outdoor',
          line: { color: '#06b6d4', width: 1.2 } },
        { x: ts, y: r.hp_temp_in, type: 'scatter', mode: 'lines', name: 'Indoor',
          line: { color: '#f97316', width: 1.5 } },
      ], {
        ...layoutBase,
        xaxis: { ...gridAxis, type: 'date' },
        yaxis: { title: 'Temperature (°C)', ...gridAxis },
        height: 240, margin: { ...layoutBase.margin, b: 50 },
      }, plotCfg);
    } else {
      Plotly.purge('hems-plot-hp');
      document.getElementById('hems-plot-hp').innerHTML = '';
      Plotly.purge('hems-plot-hp-temp');
      document.getElementById('hems-plot-hp-temp').innerHTML = '';
    }

    // 5. EV Dedicated Breakdown (per-vehicle charge + SoC + trip shading)
    if (r.ev_enabled && r.ev_units && r.ev_units.length > 0) {
      const traces5 = [];
      const evShapes = [];
      const evAnnotations = [];
      r.ev_units.forEach((ev, i) => {
        const col = unitPalette[i % unitPalette.length];
        traces5.push({ x: ts, y: ev.ch, type: 'bar', name: ev.name + ' Charge',
          marker: { color: col }, opacity: 0.65 });
        traces5.push({ x: ts, y: ev.soc, type: 'scatter', mode: 'lines',
          name: ev.name + ' SoC', yaxis: 'y2',
          line: { color: col, width: 2, dash: 'dot' } });
        // Build trip-away shapes from the availability array
        if (ev.avail) {
          let inTrip = false;
          let tripStart = null;
          let tripStartIdx = 0;
          for (let t = 0; t <= ev.avail.length; t++) {
            const away = t < ev.avail.length ? ev.avail[t] < 0.5 : false;
            if (away && !inTrip) {
              inTrip = true;
              tripStart = ts[t];
              tripStartIdx = t;
            } else if (!away && inTrip) {
              inTrip = false;
              const tripEnd = ts[Math.min(t, ts.length - 1)];
              evShapes.push({
                type: 'rect', xref: 'x', yref: 'paper',
                x0: tripStart, x1: tripEnd, y0: 0, y1: 1,
                fillcolor: col, opacity: 0.10,
                line: { color: col, width: 1.5, dash: 'dash' },
              });
              // Label at midpoint of the trip region
              const midIdx = Math.floor((tripStartIdx + t) / 2);
              if (midIdx < ts.length) {
                evAnnotations.push({
                  x: ts[midIdx], y: 1, xref: 'x', yref: 'paper',
                  text: '🚗 ' + ev.name + ' away',
                  showarrow: false,
                  font: { size: 9, color: col },
                  yanchor: 'bottom',
                });
              }
            }
          }
        }
      });
      Plotly.newPlot('hems-plot-ev', traces5, {
        ...layoutBase,
        xaxis: { ...gridAxis, type: 'date' },
        yaxis: { title: 'Charge Power (kW)', ...gridAxis, rangemode: 'tozero' },
        yaxis2: { title: 'SoC (kWh)', overlaying: 'y', side: 'right',
          ...gridAxis, rangemode: 'tozero' },
        barmode: 'group',
        height: 340,
        shapes: evShapes,
        annotations: evAnnotations,
      }, plotCfg);
    } else {
      Plotly.purge('hems-plot-ev');
      document.getElementById('hems-plot-ev').innerHTML = '';
    }

    // ── Wire range sync: overview chart zoom/buttons drive all other charts ──
    const rangeDiv = document.getElementById('hems-plot-range');
    rangeDiv.removeAllListeners && rangeDiv.removeAllListeners('plotly_relayout');
    rangeDiv.on('plotly_relayout', function(ed) {
      if (syncingRange) return;
      let range = null;
      if (ed['xaxis.range[0]'] && ed['xaxis.range[1]']) {
        range = [ed['xaxis.range[0]'], ed['xaxis.range[1]']];
      } else if (ed['xaxis.range']) {
        range = ed['xaxis.range'];
      }
      // autorange or rangeselector button reset
      const isReset = ed['xaxis.autorange'] || (!range && Object.keys(ed).some(k => k.startsWith('xaxis.range')));
      if (!range && !isReset) return;
      syncingRange = true;
      const driven = ['hems-plot-prices', 'hems-plot-cost', 'hems-plot-grid', 'hems-plot-power',
        'hems-plot-soc', 'hems-plot-pv', 'hems-plot-pv-curt', 'hems-plot-hp', 'hems-plot-hp-temp', 'hems-plot-ev'];
      driven.forEach(id => {
        const div = document.getElementById(id);
        if (div && div.data && div.data.length > 0) {
          if (range) {
            Plotly.relayout(div, { 'xaxis.range[0]': range[0], 'xaxis.range[1]': range[1] });
          } else {
            Plotly.relayout(div, { 'xaxis.autorange': true });
          }
        }
      });
      syncingRange = false;
    });
  }

  // ── Theme change observer — re-apply Plotly colours ──
  const themeObserver = new MutationObserver(function() {
    const c = plotlyColors();
    const update = {
      'paper_bgcolor': c.paper_bgcolor,
      'plot_bgcolor': c.plot_bgcolor,
      'font.color': c.fontColor,
      'xaxis.gridcolor': c.gridColor,
      'xaxis.zerolinecolor': c.zeroColor,
      'yaxis.gridcolor': c.gridColor,
      'yaxis.zerolinecolor': c.zeroColor,
      'title.font.color': c.fontColor,
    };
    PLOT_IDS.forEach(id => {
      const div = document.getElementById(id);
      if (div && div.data && div.data.length > 0) {
        Plotly.relayout(div, update).catch(() => {});
      }
    });
  });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  init();
})();
</script>
