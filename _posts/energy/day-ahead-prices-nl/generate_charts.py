#!/usr/bin/env python3
"""
Generate interactive Plotly bar charts for Dutch day-ahead electricity prices.

uv run --with pandas --with plotly generate_charts.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("../../../assets/plotly")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
YEARS = list(range(2019, 2026))

# Dark mode theme script injected into each chart HTML.
# Detects the parent page's data-theme attribute and applies matching colors.
THEME_SCRIPT = """
<style>
  html, body {
    background: transparent !important;
    margin: 0;
    padding: 0;
  }
</style>
<script>
(function() {
  var LIGHT = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(240,240,240,0.5)',
    'font.color': '#2a3f5f',
    'xaxis.gridcolor': '#ccc',
    'xaxis.zerolinecolor': '#ccc',
    'xaxis.tickfont.color': '#2a3f5f',
    'xaxis.title.font.color': '#2a3f5f',
    'yaxis.gridcolor': '#ccc',
    'yaxis.zerolinecolor': '#ccc',
    'yaxis.tickfont.color': '#2a3f5f',
    'yaxis.title.font.color': '#2a3f5f',
    'legend.font.color': '#2a3f5f',
    'title.font.color': '#2a3f5f'
  };
  var DARK = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(255,255,255,0.06)',
    'font.color': '#c9d1d9',
    'xaxis.gridcolor': 'rgba(255,255,255,0.12)',
    'xaxis.zerolinecolor': 'rgba(255,255,255,0.12)',
    'xaxis.tickfont.color': '#c9d1d9',
    'xaxis.title.font.color': '#c9d1d9',
    'yaxis.gridcolor': 'rgba(255,255,255,0.12)',
    'yaxis.zerolinecolor': 'rgba(255,255,255,0.12)',
    'yaxis.tickfont.color': '#c9d1d9',
    'yaxis.title.font.color': '#c9d1d9',
    'legend.font.color': '#c9d1d9',
    'title.font.color': '#c9d1d9'
  };

  function getTheme() {
    try {
      var t = window.parent.document.documentElement.getAttribute('data-theme');
      if (t) return t;
    } catch(e) {}
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme() {
    var gd = document.querySelector('.js-plotly-plot');
    if (!gd) return;
    var t = getTheme();
    var colors = t === 'dark' ? DARK : LIGHT;
    // Update dropdown button backgrounds
    var menus = (gd.layout && gd.layout.updatemenus) || [];
    var newMenus = menus.map(function(m) {
      return Object.assign({}, m, {
        bgcolor: t === 'dark' ? 'rgba(50,50,60,0.9)' : 'rgba(255,255,255,0.8)',
        bordercolor: t === 'dark' ? '#666' : '#333',
        font: {color: t === 'dark' ? '#dee2e6' : '#2a3f5f'}
      });
    });
    var update = Object.assign({}, colors);
    if (newMenus.length) update.updatemenus = newMenus;
    Plotly.relayout(gd, update);
  }

  // Apply on load and watch for changes
  if (document.readyState === 'complete') {
    setTimeout(applyTheme, 100);
  } else {
    window.addEventListener('load', function() { setTimeout(applyTheme, 100); });
  }
  try {
    var obs = new MutationObserver(function(muts) {
      muts.forEach(function(m) { if (m.attributeName === 'data-theme') applyTheme(); });
    });
    obs.observe(window.parent.document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
  } catch(e) {}
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
})();
</script>
"""


def inject_theme_script(html_str):
    """Inject the dark mode theme script into the HTML."""
    return html_str.replace("</body>", THEME_SCRIPT + "\n</body>")


def create_color_gradient(hex_color, num_shades=5):
    """Create a gradient of colors from a base hex color."""
    # Convert hex to RGB
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    # Create gradient by adjusting brightness
    # Range from darkest to lightest
    gradient = []
    for i in range(num_shades):
        # Factor ranges from 0.6 (darkest) to 1.0 (base color/lightest)
        factor = 0.6 + (0.4 * i / (num_shades - 1))
        new_r = min(255, int(r * factor))
        new_g = min(255, int(g * factor))
        new_b = min(255, int(b * factor))
        gradient.append(f"#{new_r:02x}{new_g:02x}{new_b:02x}")

    return gradient


def load_and_process_data(year):
    """Load and aggregate price data for a given year."""
    filepath = DATA_DIR / f"jeroen_punt_nl_dynamische_stroomprijzen_jaar_{year}.csv"

    # Read CSV with semicolon separator
    df = pd.read_csv(filepath, sep=";", parse_dates=["datum_nl"])

    # Convert price column (replace comma with dot for decimal)
    df["prijs_excl_belastingen"] = (
        df["prijs_excl_belastingen"].str.replace(",", ".").astype(float)
    )

    # Extract month and calculate monthly average
    df["month"] = df["datum_nl"].dt.month
    monthly_avg = df.groupby("month")["prijs_excl_belastingen"].mean().reset_index()
    monthly_avg["year"] = year

    return monthly_avg


def create_interactive_chart():
    """Create an interactive bar chart with year selector."""
    # Load data for all years
    all_data = []
    for year in YEARS:
        try:
            data = load_and_process_data(year)
            all_data.append(data)
        except FileNotFoundError:
            print(f"Warning: Data file for year {year} not found, skipping...")
            continue

    if not all_data:
        print("Error: No data files found!")
        return

    # Create figure
    fig = go.Figure()

    # Month names for x-axis
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # Add traces for each year
    for i, year_data in enumerate(all_data):
        year = year_data["year"].iloc[0]

        fig.add_trace(
            go.Bar(
                x=month_names[: len(year_data)],
                y=year_data["prijs_excl_belastingen"],
                name=str(year),
                visible=(
                    i == len(all_data) - 1
                ),  # Only show most recent year by default
                marker=dict(
                    color=year_data["prijs_excl_belastingen"],
                    colorscale="RdYlGn_r",  # Red (high) to Green (low)
                    showscale=True,
                    colorbar=dict(title="Price (€/kWh)", x=1.15),
                    line=dict(color="rgb(8,48,107)", width=1.5),
                ),
                text=year_data["prijs_excl_belastingen"].round(4),
                texttemplate="€%{text:.4f}",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>"
                + "Average Price: €%{y:.4f}/kWh<br>"
                + "<extra></extra>",
            )
        )

    # Create dropdown buttons
    buttons = []
    for i, year_data in enumerate(all_data):
        year = year_data["year"].iloc[0]

        # Create visibility list (True for selected year, False for others)
        visibility = [False] * len(all_data)
        visibility[i] = True

        buttons.append(
            dict(
                label=str(year),
                method="update",
                args=[
                    {"visible": visibility},
                    {
                        "title": f"Dutch Day-Ahead Electricity Prices - {year}<br><sub>Monthly Average (excl. taxes)</sub>"
                    },
                ],
            )
        )

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"Dutch Day-Ahead Electricity Prices - {all_data[-1]['year'].iloc[0]}<br><sub>Monthly Average (excl. taxes)</sub>",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Month",
            tickfont_size=14,
        ),
        yaxis=dict(
            title="Average Price (€/kWh)",
            tickfont_size=14,
        ),
        updatemenus=[
            dict(
                active=len(all_data) - 1,
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#333",
                borderwidth=2,
            )
        ],
        annotations=[
            dict(
                text="Select Year:",
                showarrow=False,
                x=1.0,
                y=1.20,
                xref="paper",
                yref="paper",
                align="right",
                xanchor="right",
                yanchor="top",
                font=dict(size=14),
            )
        ],
        height=600,
        showlegend=False,
        hovermode="x unified",
        bargap=0.15,
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Save to HTML with theme support
    output_file = OUTPUT_DIR / "day_ahead_prices_nl.html"
    html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
    with open(str(output_file), "w") as f:
        f.write(inject_theme_script(html_str))
    print(f"Chart saved to: {output_file}")

    return fig


def create_yearly_comparison_chart():
    """Create a grouped bar chart comparing all years side by side."""
    # Load data for all years
    all_data = []
    for year in YEARS:
        try:
            data = load_and_process_data(year)
            all_data.append(data)
        except FileNotFoundError:
            print(f"Warning: Data file for year {year} not found, skipping...")
            continue

    if not all_data:
        print("Error: No data files found!")
        return

    # Create figure
    fig = go.Figure()

    # Month names for x-axis
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # Color palette for years
    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
    ]

    # Add traces for each year
    for i, year_data in enumerate(all_data):
        year = year_data["year"].iloc[0]

        fig.add_trace(
            go.Bar(
                x=month_names[: len(year_data)],
                y=year_data["prijs_excl_belastingen"],
                name=str(year),
                marker=dict(
                    color=colors[i % len(colors)],
                    line=dict(color="rgb(8,48,107)", width=0.5),
                ),
                hovertemplate="<b>%{x} "
                + str(year)
                + "</b><br>"
                + "Avg Price: €%{y:.4f}/kWh<br>"
                + "<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title=dict(
            text="Dutch Day-Ahead Electricity Prices Comparison<br><sub>Monthly Average (excl. taxes) - All Years</sub>",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Month",
            tickfont_size=14,
        ),
        yaxis=dict(
            title="Average Price (€/kWh)",
            tickfont_size=14,
        ),
        barmode="group",
        height=600,
        legend=dict(
            title="Year", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02
        ),
        hovermode="x unified",
        bargap=0.15,
        bargroupgap=0.1,
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Save to HTML with theme support
    output_file = OUTPUT_DIR / "day_ahead_prices_nl_comparison.html"
    html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
    with open(str(output_file), "w") as f:
        f.write(inject_theme_script(html_str))
    print(f"Comparison chart saved to: {output_file}")

    return fig


def load_hourly_data(year):
    """Load raw hourly price data for spread analysis."""
    filepath = DATA_DIR / f"jeroen_punt_nl_dynamische_stroomprijzen_jaar_{year}.csv"

    # Read CSV with semicolon separator
    df = pd.read_csv(filepath, sep=";", parse_dates=["datum_nl"])

    # Convert price column (replace comma with dot for decimal)
    df["prijs_excl_belastingen"] = (
        df["prijs_excl_belastingen"].str.replace(",", ".").astype(float)
    )

    # Extract date only (without time)
    df["date"] = df["datum_nl"].dt.date
    df["hour"] = df["datum_nl"].dt.hour
    df["minute"] = df["datum_nl"].dt.minute

    return df


def calculate_daily_spreads(year, window_hours, smoothing_days=7):
    """
    Calculate daily price metrics for different time windows.

    Returns DataFrame with:
    - spread: (average of most expensive X hours) - (average of cheapest X hours)
    - most_expensive: average of most expensive X hours
    - cheapest: average of cheapest X hours
    where X = window_hours
    """
    df = load_hourly_data(year)

    # Number of 15-minute intervals in the window
    window_size = window_hours * 4

    # Calculate metrics for each day
    def calc_metrics(group):
        prices = group["prijs_excl_belastingen"].values
        if len(prices) < window_size * 2:  # Need at least 2x window size for comparison
            return pd.Series({"spread": None, "most_expensive": None, "cheapest": None})

        # Sort prices to find most expensive and cheapest periods
        sorted_prices = sorted(prices, reverse=True)

        # Average of most expensive X hours (top window_size intervals)
        avg_expensive = sum(sorted_prices[:window_size]) / window_size

        # Average of cheapest X hours (bottom window_size intervals)
        avg_cheap = sum(sorted_prices[-window_size:]) / window_size

        # Spread is the difference
        spread = avg_expensive - avg_cheap

        return pd.Series({
            "spread": spread,
            "most_expensive": avg_expensive,
            "cheapest": avg_cheap
        })

    daily_metrics = df.groupby("date").apply(calc_metrics).reset_index()
    daily_metrics = daily_metrics.dropna()  # Remove any days with insufficient data
    daily_metrics["window_hours"] = window_hours

    # Apply rolling mean to smooth the data
    if smoothing_days > 1:
        daily_metrics = daily_metrics.sort_values("date")
        daily_metrics["spread"] = (
            daily_metrics["spread"]
            .rolling(window=smoothing_days, center=True, min_periods=1)
            .mean()
        )
        daily_metrics["most_expensive"] = (
            daily_metrics["most_expensive"]
            .rolling(window=smoothing_days, center=True, min_periods=1)
            .mean()
        )
        daily_metrics["cheapest"] = (
            daily_metrics["cheapest"]
            .rolling(window=smoothing_days, center=True, min_periods=1)
            .mean()
        )

    return daily_metrics


def create_spread_analysis_chart():
    """Create line chart showing daily price spreads for different time windows."""
    # Define time windows to analyze
    time_windows = [1, 2, 4, 6, 8]
    smoothing_periods = [1, 7, 30]  # Days for rolling mean
    metrics = ["spread", "most_expensive", "cheapest"]

    # Load data for all years, windows, and smoothing periods
    all_data = {}
    for smoothing_days in smoothing_periods:
        all_year_data = {}
        for year in YEARS:
            try:
                year_spreads = {}
                for window in time_windows:
                    spread_data = calculate_daily_spreads(year, window, smoothing_days)
                    year_spreads[window] = spread_data
                all_year_data[year] = year_spreads
            except FileNotFoundError:
                print(f"Warning: Data file for year {year} not found, skipping...")
                continue
        all_data[smoothing_days] = all_year_data

    if not all_data:
        print("Error: No data files found!")
        return

    # Create figure
    fig = go.Figure()

    # Base colors for different years
    year_base_colors = {
        2019: "#1f77b4",  # blue
        2020: "#ff7f0e",  # orange
        2021: "#2ca02c",  # green
        2022: "#d62728",  # red
        2023: "#9467bd",  # purple
        2024: "#8c564b",  # brown
        2025: "#e377c2",  # pink
    }

    # Create color gradients for each year (one for each time window)
    year_color_gradients = {}
    for year, base_color in year_base_colors.items():
        year_color_gradients[year] = create_color_gradient(
            base_color, num_shades=len(time_windows)
        )

    # Map window index to color for each year
    window_to_gradient_index = {window: i for i, window in enumerate(time_windows)}

    # Marker symbols for different years
    year_markers = {
        2019: "circle",
        2020: "square",
        2021: "diamond",
        2022: "cross",
        2023: "x",
        2024: "triangle-up",
        2025: "star",
    }

    # Line styles for different time windows
    window_line_styles = {
        1: "solid",
        2: "dash",
        4: "dot",
        6: "dashdot",
        8: "longdash",
    }

    # Add traces for each metric, smoothing period, year, and time window
    for metric in metrics:
        for smoothing_days in smoothing_periods:
            all_year_data = all_data[smoothing_days]
            for year in sorted(all_year_data.keys()):
                for window in time_windows:
                    spread_data = all_year_data[year][window].copy()

                    # Convert date to datetime for proper x-axis
                    spread_data["original_date"] = pd.to_datetime(spread_data["date"])

                    # Normalize all years to same reference year (2024) for overlay comparison
                    spread_data["normalized_date"] = spread_data["original_date"].apply(
                        lambda x: x.replace(year=2024)
                    )

                    # Get gradient color for this year and window
                    gradient_index = window_to_gradient_index[window]
                    window_color = year_color_gradients[year][gradient_index]

                    # Format metric name for display
                    metric_label = {
                        "spread": "Spread",
                        "most_expensive": "Most Expensive",
                        "cheapest": "Cheapest"
                    }[metric]

                    fig.add_trace(
                        go.Scatter(
                            x=spread_data["normalized_date"],
                            y=spread_data[metric],
                            name=f"{window}h",
                            legendgroup=f"year_{year}_{metric}",
                            legendgrouptitle_text=f"{year}",
                            mode="lines+markers",
                            line=dict(
                                color=window_color,
                                width=2.5 if year == max(all_year_data.keys()) else 2,
                                dash=window_line_styles.get(window, "solid"),
                            ),
                            marker=dict(
                                symbol=year_markers.get(year, "circle"),
                                size=4,
                                color=window_color,
                            ),
                            opacity=0.85 if year == max(all_year_data.keys()) else 0.7,
                            visible=(
                                metric == "spread" and smoothing_days == 7
                            ),  # Show spread with 7-day smoothing by default
                            showlegend=True,
                            hovertemplate=f"<b>%{{x|%b %d}} ({year})</b><br>"
                            + f"{window}-hour window<br>"
                            + f"{metric_label}: €%{{y:.4f}}/kWh<br>"
                            + "<extra></extra>",
                        )
                    )

    # Calculate number of traces per combination
    traces_per_smoothing = len(YEARS) * len(time_windows)
    traces_per_metric = traces_per_smoothing * len(smoothing_periods)

    # Create dropdown buttons for metric selection
    # Using method="skip" so custom JavaScript handles the coupled state between dropdowns
    metric_labels_map = {
        "spread": "Spread",
        "most_expensive": "Most Expensive",
        "cheapest": "Cheapest"
    }
    metric_buttons = []
    for metric_idx, metric in enumerate(metrics):
        metric_buttons.append(
            dict(
                label=metric_labels_map[metric],
                method="skip",
                args=[None],
            )
        )

    # Create dropdown buttons for smoothing period selection
    # Using method="skip" so custom JavaScript handles the coupled state between dropdowns
    smoothing_buttons = []
    for smoothing_idx, smoothing_days in enumerate(smoothing_periods):
        smoothing_label = (
            "No smoothing" if smoothing_days == 1 else f"{smoothing_days}-day avg"
        )
        smoothing_buttons.append(
            dict(
                label=smoothing_label,
                method="skip",
                args=[None],
            )
        )

    # Update layout
    fig.update_layout(
        title=dict(
            text="Daily Price Analysis (All Years)<br><sub>Spread and price extremes within different time windows</sub>",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Date",
            tickfont_size=14,
            rangeslider=dict(
                visible=True,
                thickness=0.05,
            ),
            tickformat="%b",
            dtick="M1",
        ),
        yaxis=dict(
            title="Price (€/kWh)",
            tickfont_size=14,
        ),
        updatemenus=[
            dict(
                active=0,  # Spread is default
                buttons=metric_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.70,
                xanchor="left",
                y=1.15,
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#333",
                borderwidth=2,
            ),
            dict(
                active=1,  # 7-day smoothing is default (index 1)
                buttons=smoothing_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#333",
                borderwidth=2,
            )
        ],
        height=700,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            tracegroupgap=20,
            groupclick="toggleitem",
        ),
        hovermode="closest",
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Save to HTML with custom JavaScript for coupled dropdown state
    output_file = OUTPUT_DIR / "day_ahead_prices_nl_spread_analysis.html"
    total_traces = len(metrics) * len(smoothing_periods) * traces_per_smoothing

    # JavaScript that synchronizes the two dropdowns and preserves legend
    # toggle state: when either dropdown changes, it captures which traces
    # in the current group are 'legendonly' (hidden via legend click), then
    # applies the same pattern to the new group.
    coupled_dropdown_js = f"""<script>
(function() {{
    var gd = document.querySelector('.js-plotly-plot');
    var TPS = {traces_per_smoothing};
    var TPM = {traces_per_metric};
    var TOT = {total_traces};

    // Track the previous dropdown state (defaults match initial layout)
    var prevM = 0, prevS = 1;

    function groupStart(m, s) {{ return m * TPM + s * TPS; }}

    gd.on('plotly_buttonclicked', function() {{
        // Capture legend toggle state from the OLD (still-current) group
        var os = groupStart(prevM, prevS);
        var legendState = [];
        for (var j = 0; j < TPS; j++) {{
            legendState.push(gd.data[os + j].visible === 'legendonly' ? 'legendonly' : true);
        }}

        // Use setTimeout so the updatemenus active indices are updated first
        setTimeout(function() {{
            var m = gd.layout.updatemenus[0].active;
            var s = gd.layout.updatemenus[1].active;
            var ns = groupStart(m, s);

            // Build visibility: new group gets old legend state, rest hidden
            var v = [];
            for (var i = 0; i < TOT; i++) {{
                v.push(i >= ns && i < ns + TPS ? legendState[i - ns] : false);
            }}
            Plotly.restyle(gd, {{visible: v}});

            prevM = m;
            prevS = s;
        }}, 0);
    }});
}})();
</script>"""

    html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
    html_str = html_str.replace("</body>", coupled_dropdown_js + "\n</body>")
    html_str = inject_theme_script(html_str)

    with open(str(output_file), "w") as f:
        f.write(html_str)

    print(f"Spread analysis chart saved to: {output_file}")

    return fig


def load_hourly_resampled(year):
    """Load 15-min data and downsample to hourly averages."""
    filepath = DATA_DIR / f"jeroen_punt_nl_dynamische_stroomprijzen_jaar_{year}.csv"
    df = pd.read_csv(filepath, sep=";", parse_dates=["datum_nl"])
    df["prijs_excl_belastingen"] = (
        df["prijs_excl_belastingen"].str.replace(",", ".").astype(float)
    )
    # Resample to hourly by flooring to the hour and averaging
    df["hour_ts"] = df["datum_nl"].dt.floor("h")
    hourly = df.groupby("hour_ts")["prijs_excl_belastingen"].mean().reset_index()
    hourly.columns = ["timestamp", "price"]
    hourly["year"] = year
    hourly["month"] = hourly["timestamp"].dt.month
    hourly["month_name"] = hourly["timestamp"].dt.strftime("%b")
    return hourly


def create_negative_price_frequency_chart():
    """
    Create a grouped bar chart showing negative-price frequency per month.

    Dropdown to switch between:
      - Count of hours with price <= -0.01 €/kWh
      - Cumulative sum of negative prices (absolute value, €/kWh)

    All years shown simultaneously with legend toggles. Dropdown preserves
    legend toggle state using custom JS (like the spread analysis chart).
    """
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2",
    ]

    all_year_stats = {}
    for year in YEARS:
        try:
            hourly = load_hourly_resampled(year)
        except FileNotFoundError:
            continue
        neg = hourly[hourly["price"] <= -0.01].copy()
        count_per_month = neg.groupby("month")["price"].count()
        sum_per_month = neg.groupby("month")["price"].sum()
        # Reindex to full 12 months
        count_per_month = count_per_month.reindex(range(1, 13), fill_value=0)
        sum_per_month = sum_per_month.reindex(range(1, 13), fill_value=0.0)
        all_year_stats[year] = {
            "count": count_per_month,
            "sum": sum_per_month,
        }

    fig = go.Figure()
    sorted_years = sorted(all_year_stats.keys())
    n_years = len(sorted_years)
    metrics = ["count", "sum"]
    traces_per_metric = n_years  # one trace per year per metric

    # Layout: [count_y1, count_y2, ..., count_yN, sum_y1, sum_y2, ..., sum_yN]
    for metric_idx, metric in enumerate(metrics):
        for yi, year in enumerate(sorted_years):
            stats = all_year_stats[year]
            color = colors[yi % len(colors)]

            if metric == "count":
                y_vals = stats["count"].values
                hover = (
                    f"<b>%{{x}} {year}</b><br>"
                    "Negative hours: %{y}<br>"
                    "<extra></extra>"
                )
            else:
                # Flip sign so bars go upward (absolute cumulative cost)
                y_vals = stats["sum"].abs().values.round(4)
                hover = (
                    f"<b>%{{x}} {year}</b><br>"
                    "Total negative cost: €%{y:.4f}/kWh<br>"
                    "<extra></extra>"
                )

            fig.add_trace(
                go.Bar(
                    x=month_names,
                    y=y_vals,
                    name=str(year),
                    legendgroup=str(year),
                    showlegend=(metric_idx == 0),
                    marker=dict(color=color, line=dict(color="rgb(8,48,107)", width=0.5)),
                    visible=(metric_idx == 0),  # count visible by default
                    hovertemplate=hover,
                )
            )

    # Dropdown uses method="skip" so custom JS handles coupled state
    metric_buttons = [
        dict(label="Count of negative hours", method="skip", args=[None]),
        dict(label="Sum of negative prices", method="skip", args=[None]),
    ]

    fig.update_layout(
        title=dict(
            text="Negative Electricity Price Frequency<br><sub>Hours with price ≤ −0.01 €/kWh per month (hourly data)</sub>",
            font=dict(size=20),
        ),
        xaxis=dict(title="Month", tickfont_size=14),
        yaxis=dict(
            title="Number of hours with price ≤ −0.01 €/kWh",
            tickfont_size=14,
        ),
        updatemenus=[
            dict(
                active=0,
                buttons=metric_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#333",
                borderwidth=2,
            )
        ],
        barmode="group",
        height=600,
        legend=dict(
            title="Year",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
        ),
        hovermode="x unified",
        bargap=0.15,
        bargroupgap=0.1,
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Custom JS to preserve legend toggle state across dropdown changes
    total_traces = len(metrics) * n_years
    y_titles = [
        "Number of hours with price ≤ −0.01 €/kWh",
        "Cumulative negative price (€/kWh)",
    ]
    coupled_js = f"""<script>
(function() {{
    var gd = document.querySelector('.js-plotly-plot');
    var NY = {n_years};
    var TOT = {total_traces};
    var YTITLES = {y_titles};
    var prev = 0;

    gd.on('plotly_buttonclicked', function() {{
        var os = prev * NY;
        var legendState = [];
        for (var j = 0; j < NY; j++) {{
            legendState.push(gd.data[os + j].visible === 'legendonly' ? 'legendonly' : true);
        }}
        setTimeout(function() {{
            var m = gd.layout.updatemenus[0].active;
            var ns = m * NY;
            var v = [];
            for (var i = 0; i < TOT; i++) {{
                if (i >= ns && i < ns + NY) {{
                    v.push(legendState[i - ns]);
                }} else {{
                    v.push(false);
                }}
            }}
            var sl = [];
            for (var i = 0; i < TOT; i++) {{
                sl.push(i >= ns && i < ns + NY);
            }}
            Plotly.restyle(gd, {{visible: v, showlegend: sl}});
            Plotly.relayout(gd, {{'yaxis.title.text': YTITLES[m]}});
            prev = m;
        }}, 0);
    }});
}})();
</script>"""

    output_file = OUTPUT_DIR / "day_ahead_prices_nl_negative_frequency.html"
    html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
    html_str = html_str.replace("</body>", coupled_js + "\n</body>")
    html_str = inject_theme_script(html_str)
    with open(str(output_file), "w") as f:
        f.write(html_str)
    print(f"Negative price frequency chart saved to: {output_file}")
    return fig


def create_hourly_price_histogram_chart():
    """
    Create overlaid histograms of hourly prices per month (5-cent bins).

    Dropdown to select the month.  All years shown simultaneously with
    legend toggles.  Dropdown preserves legend toggle state via custom JS.
    Bins are aligned so that 0.00 is always a bin edge.
    """
    import numpy as np

    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    month_names_full = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2",
    ]

    # Load hourly data for every year
    yearly_hourly = {}
    for year in YEARS:
        try:
            yearly_hourly[year] = load_hourly_resampled(year)
        except FileNotFoundError:
            continue

    sorted_years = sorted(yearly_hourly.keys())
    n_years = len(sorted_years)

    # Determine global bin edges in steps of 0.05 €/kWh, aligned to 0.00
    all_prices = pd.concat([df["price"] for df in yearly_hourly.values()])
    price_min = all_prices.min()
    price_max = all_prices.max()
    # Extend from 0.00 outward in both directions to guarantee 0.00 is an edge
    neg_edge = -0.05 * np.ceil(abs(min(price_min, 0)) / 0.05)
    pos_edge = 0.05 * np.ceil(max(price_max, 0) / 0.05)
    bin_edges = np.arange(neg_edge, pos_edge + 0.05, 0.05)
    # Round to avoid floating-point drift
    bin_edges = np.round(bin_edges, 4)
    bin_centers = np.round((bin_edges[:-1] + bin_edges[1:]) / 2, 4)

    fig = go.Figure()

    # Track per-month-per-year price ranges for dynamic x-axis adjustment
    # month_year_ranges[month_idx][year_idx] = [lo, hi] or null if no data
    month_year_ranges = []

    # For each month, for each year add one Bar trace
    # Default visible: January (month index 0)
    for month_idx in range(12):
        month_num = month_idx + 1
        year_ranges = []
        for yi, year in enumerate(sorted_years):
            df = yearly_hourly[year]
            month_data = df[df["month"] == month_num]["price"]
            if len(month_data) > 0:
                lo = float(np.floor(month_data.min() / 0.05) * 0.05 - 0.05)
                hi = float(np.ceil(month_data.max() / 0.05) * 0.05 + 0.05)
                year_ranges.append([round(lo, 4), round(hi, 4)])
            else:
                year_ranges.append(None)
            counts, _ = np.histogram(month_data, bins=bin_edges)

            fig.add_trace(
                go.Bar(
                    x=bin_centers.tolist(),
                    y=counts.tolist(),
                    name=str(year),
                    legendgroup=str(year),
                    showlegend=(month_idx == 0),
                    marker=dict(
                        color=colors[yi % len(colors)],
                        line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
                    ),
                    visible=(month_idx == 0),
                    hovertemplate=(
                        f"<b>{month_names[month_idx]} {year}</b><br>"
                        "Price bin: €%{x:.2f}/kWh<br>"
                        "Count: %{y} hours<br>"
                        "<extra></extra>"
                    ),
                )
            )

        month_year_ranges.append(year_ranges)

    # Compute initial x range for January from all years
    jan_lo = min(r[0] for r in month_year_ranges[0] if r is not None)
    jan_hi = max(r[1] for r in month_year_ranges[0] if r is not None)

    # Dropdown uses method="skip" so custom JS handles legend state
    total_traces = 12 * n_years
    month_buttons = []
    for month_idx in range(12):
        month_buttons.append(
            dict(
                label=month_names_full[month_idx],
                method="skip",
                args=[None],
            )
        )

    fig.update_layout(
        title=dict(
            text="Hourly Price Distribution — January<br><sub>Histogram in 5-cent bins (hourly data)</sub>",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Price (€/kWh)",
            tickfont_size=12,
            dtick=0.05,
            tickformat=".2f",
            range=[jan_lo, jan_hi],
        ),
        yaxis=dict(
            title="Number of hours",
            tickfont_size=14,
        ),
        updatemenus=[
            dict(
                active=0,
                buttons=month_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#333",
                borderwidth=2,
            )
        ],
        barmode="group",
        height=600,
        legend=dict(
            title="Year",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
        ),
        hovermode="x unified",
        bargap=0.05,
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Custom JS: preserve legend state + dynamic x range from visible years
    month_names_js = [f'"{m}"' for m in month_names_full]
    import json
    myr_json = json.dumps(month_year_ranges)
    coupled_js = f"""<script>
(function() {{
    var gd = document.querySelector('.js-plotly-plot');
    var NY = {n_years};
    var TOT = {total_traces};
    var MONTHS = [{', '.join(month_names_js)}];
    var MYR = {myr_json};
    var prev = 0;

    function calcRange(monthIdx) {{
        var ns = monthIdx * NY;
        var lo = Infinity, hi = -Infinity;
        for (var j = 0; j < NY; j++) {{
            var vis = gd.data[ns + j].visible;
            if (vis === true && MYR[monthIdx][j]) {{
                lo = Math.min(lo, MYR[monthIdx][j][0]);
                hi = Math.max(hi, MYR[monthIdx][j][1]);
            }}
        }}
        if (lo === Infinity) {{ lo = -0.1; hi = 0.5; }}
        return [lo, hi];
    }}

    // Recalc range on legend toggle
    gd.on('plotly_legendclick', function() {{
        setTimeout(function() {{
            var m = gd.layout.updatemenus[0].active;
            Plotly.relayout(gd, {{'xaxis.range': calcRange(m)}});
        }}, 50);
    }});

    gd.on('plotly_buttonclicked', function() {{
        var os = prev * NY;
        var legendState = [];
        for (var j = 0; j < NY; j++) {{
            legendState.push(gd.data[os + j].visible === 'legendonly' ? 'legendonly' : true);
        }}
        setTimeout(function() {{
            var m = gd.layout.updatemenus[0].active;
            var ns = m * NY;
            var v = [];
            var sl = [];
            for (var i = 0; i < TOT; i++) {{
                if (i >= ns && i < ns + NY) {{
                    v.push(legendState[i - ns]);
                    sl.push(true);
                }} else {{
                    v.push(false);
                    sl.push(false);
                }}
            }}
            Plotly.restyle(gd, {{visible: v, showlegend: sl}});
            Plotly.relayout(gd, {{
                'title.text': 'Hourly Price Distribution — ' + MONTHS[m] + '<br><sub>Histogram in 5-cent bins (hourly data)</sub>',
                'xaxis.range': calcRange(m)
            }});
            prev = m;
        }}, 0);
    }});
}})();
</script>"""

    output_file = OUTPUT_DIR / "day_ahead_prices_nl_hourly_histogram.html"
    html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
    html_str = html_str.replace("</body>", coupled_js + "\n</body>")
    html_str = inject_theme_script(html_str)
    with open(str(output_file), "w") as f:
        f.write(html_str)
    print(f"Hourly price histogram chart saved to: {output_file}")
    return fig


if __name__ == "__main__":
    print("Generating interactive bar charts...")
    print("-" * 50)

    # Generate main chart with year selector
    print("\n1. Creating chart with year selector...")
    create_interactive_chart()

    # Generate comparison chart
    print("\n2. Creating year comparison chart...")
    create_yearly_comparison_chart()

    # Generate spread analysis chart
    print("\n3. Creating spread analysis chart...")
    create_spread_analysis_chart()

    # Generate negative price frequency chart
    print("\n4. Creating negative price frequency chart...")
    create_negative_price_frequency_chart()

    # Generate hourly price histogram chart
    print("\n5. Creating hourly price histogram chart...")
    create_hourly_price_histogram_chart()

    print("\n" + "-" * 50)
    print("Done! Charts generated successfully.")
