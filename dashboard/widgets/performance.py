import streamlit as st
import pandas as pd
import altair as alt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from library.config import set_data_root
from widgets.utilities import scenario, full_palette
from library.language import TEXTS, MONTHS

def _text_sufficiency(data):
    data["Months"] = MONTHS

    fully = data[data["Value"] == 1.0]
    average = data[data["Value"] < 1.0]["Value"].mean()
    min = data.loc[data['Value'].idxmin()]
    
    st.divider()
    st.subheader(f'Demand is fully met in {len(fully)} months: {", ".join(fully["Months"])}')
    st.divider()
    st.subheader(f'Average for the remaining months is {"{0:.2f}".format(average * 100)}%')
    st.divider()
    st.subheader(f'The worst month is {min["Months"]} where {"{0:.2f}".format(min["Value"] * 100)}% of the demand is met')

def _big_chart(total_data, days_below):
    color_mapping = full_palette()

    fig = make_subplots(rows=1, cols=2, column_widths=[0.7, 0.3])

    fig.add_trace(
        go.Bar(
            y=total_data[total_data["type"] == "Sufficiency"]["Value"] * 100,
            marker_color=color_mapping["ON"]
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(
            y=total_data[total_data["type"] == "Shortfall"]["Value"] * 100,
            marker_color=color_mapping["OFF"]
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=days_below["Days"],
            y=days_below["Percentage"] * 100,
            marker_color=color_mapping["ON"],
            orientation='h'
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=240,
        barmode='stack',
        showlegend=False,
        yaxis=dict(title=None),
        margin=dict(t=0, b=40, l=40, r=40)
    )

    st.plotly_chart(fig, config={'displayModeBar': False})

def performance_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit):
    # State management
    data_root = set_data_root()

    data = pd.DataFrame()
    days_below = pd.DataFrame()
    sufficiency = pd.DataFrame()
    resolution = '1M'

    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / "performance_metrics.csv"
    if fname.is_file():
        data = pd.read_csv(fname)
        data.rename(columns={'Unnamed: 0': 'type'}, inplace=True)

    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / "days_below.csv"
    if fname.is_file():
        days_below = pd.read_csv(fname)
        days_below.rename(columns={'Unnamed: 0': 'Percentage'}, inplace=True)

    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / f"sufficiency_t_{resolution}.csv"
    if fname.is_file():
        sufficiency = pd.read_csv(fname)
        sufficiency.rename(columns={'0': 'Value'}, inplace=True)

    _big_chart(data, days_below)

    _text_sufficiency(sufficiency)
