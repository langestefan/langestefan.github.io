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
        paper_bgcolor="white",
    )

    # Save to HTML
    output_file = OUTPUT_DIR / "day_ahead_prices_nl.html"
    fig.write_html(
        str(output_file),
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
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
        paper_bgcolor="white",
    )

    # Save to HTML
    output_file = OUTPUT_DIR / "day_ahead_prices_nl_comparison.html"
    fig.write_html(
        str(output_file),
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        },
    )
    print(f"Comparison chart saved to: {output_file}")

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

    print("\n" + "-" * 50)
    print("Done! Charts generated successfully.")
