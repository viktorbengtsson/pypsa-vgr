import streamlit as st
import pandas as pd
import numpy as np
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
    
    text = TEXTS["demand_metric_text"].format(
        fully_length=f"{len(fully)}",
        fully_months=", ".join(fully["Months"]),
        average_percentage="{0:.2f}".format(average * 100),
        min_months=min["Months"],
        min_percentage="{0:.2f}".format(min["Value"] * 100)
    )
    st.markdown(f'<p style="font-size:14px;">{text}</p>', unsafe_allow_html=True)

def _sufficiency_charts(total_data, days_below, days_sufficient, total_energy, curtailed_energy):
    color_mapping = full_palette()

    fig = make_subplots(rows=1, cols=3, column_widths=[0.28, 0.28, 0.44], horizontal_spacing = 0.2, subplot_titles = [TEXTS["Sufficiency"], TEXTS["Production"], TEXTS["Days below"]])

    fig.add_trace(
        go.Bar(
            y=total_data[total_data["type"] == "Sufficiency"]["Value"] * 100,
            marker_color=color_mapping["ON"],
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
            y=[(total_energy / (total_energy + curtailed_energy)) * 100],
            marker_color=color_mapping["ON"],
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(
            y=[(curtailed_energy / (total_energy + curtailed_energy)) * 100],
            marker_color=color_mapping["OFF"]
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Bar(
            x=days_below["Days"],
            y=days_below["Percentage"] * 100,
            marker_color=color_mapping["OFF"],
            orientation='h'
        ),
        row=1, col=3
    )
    #fig.add_trace(
    #    go.Bar(
    #        x=[days_sufficient],
    #        y=[100],
    #        marker_color=color_mapping["ON"],
    #        orientation='h'
    #    ),
    #    row=1, col=3
    #)

    fig.update_annotations(font_size=16, font_color="black", height=60)
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=2)
    fig.update_xaxes(title=TEXTS["Number of days"], row=1, col=3)
    fig.update_yaxes(dict(
        title=None,
        range=[0, 100],
        tickmode='array',
        tickvals=[0, 25, 50, 75, 100]
    ), row=1, col=1)
    fig.update_yaxes(dict(
        title=None,
        range=[0, 100],
        tickmode='array',
        tickvals=[0, 25, 50, 75, 100]
    ), row=1, col=2)
    fig.update_yaxes(dict(
        title=None,
        range=[0, 100],
        tickmode='array',
        tickvals=[0, 25, 50, 75, 95]
    ), row=1, col=3)

    fig.update_layout(
        height=384,
        barmode='stack',
        showlegend=False,
        margin=dict(t=45, b=40, l=40, r=40)
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

    curtailed_energy = []
    total_energies = []
    for gen in ['solar', 'onwind', 'offwind']:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / gen / 'details.csv'
        if fname.is_file():
            details = pd.read_csv(fname, index_col=0)
            total_energies.append(details.loc['total_energy'][gen])
            curtailed_energy.append(details.loc['total_energy'][gen] * ( 1 / (1-details.loc['curtailment'][gen]) - 1 ))


    total_energy = sum(data[data["type"] == "Total energy"]["Value"]) #sum(total_energies)
    curtailed_energy = sum(np.nan_to_num(curtailed_energy, nan=0))

    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / "days_below.csv"
    if fname.is_file():
        days_below = pd.read_csv(fname)
        days_below.rename(columns={'Unnamed: 0': 'Percentage'}, inplace=True)

    days_sufficient = 365 - sum(days_below["Days"])

    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / f"sufficiency_t_{resolution}.csv"
    if fname.is_file():
        sufficiency = pd.read_csv(fname)
        sufficiency.rename(columns={'0': 'Value'}, inplace=True)

    with st.container(border=True):
        _sufficiency_charts(data, days_below, days_sufficient, total_energy, curtailed_energy)

        _text_sufficiency(sufficiency)
