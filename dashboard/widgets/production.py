import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from library.config import set_data_root
from widgets.utilities import scenario, full_palette
from library.language import TEXTS

def _big_chart(power, store, demand):
    color_mapping = full_palette()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for type in power['type'].unique():
        filtered_data = power[power['type'] == type]
        if type not in color_mapping:
            raise Exception(f"Cannot find {type} in color mapping")
        fig.add_trace(
            go.Bar(
                x=filtered_data["snapshot"], 
                y=filtered_data["value"], 
                marker_color=color_mapping[type],
                hovertemplate=str(type + ': %{x}<br>%{y}'),
                name=type
            ),
            secondary_y=False
        )
    '''
    for type in store['type'].unique():
        filtered_data = store[store['type'] == type]
        if type not in color_mapping:
            raise Exception(f"Cannot find {type} in color mapping")
        fig.add_trace(
            go.Bar(
                x=filtered_data["snapshot"], 
                y=filtered_data["value"], 
                marker_color=color_mapping[type],
                yaxis="y2",
                hovertemplate=str(type + ': %{x}<br>%{y}'),
                name=type
            ),
            secondary_y=True
        )
    '''
    fig.add_trace(
        go.Scatter(
            x=demand["snapshot"],
            y=demand["value"],
            name=TEXTS["Demand"],
            mode="lines+markers",
            marker_color=color_mapping["demand"],
        ),
        secondary_y=False
    )

    fig.update_layout(
        height=340,
        barmode='stack',
        showlegend=False,
        yaxis=dict(title=None),
        yaxis2=dict(title=None, overlaying='y', side='right'),
        margin=dict(t=0, b=40, l=0, r=0)
    )
    fig.update_xaxes(dict(
        title=None,
        dtick='M1',
        tickformat='%b',
        range=[min(filtered_data["snapshot"]), max(filtered_data["snapshot"])]
    ))

    # FIXA SÅ DET ÄR BARA ENA...
    fig.update_yaxes(dict(
        title=None,
        showgrid=False,
        ticks='',
        showticklabels=False
    ), secondary_y=True)

    #min_y = min(pd.concat([power["value"], store["value"], demand["value"]])) * 1.1
    #max_y = max(pd.concat([power["value"], store["value"], demand["value"]])) * 1.1
    min_y = min(pd.concat([power["value"], demand["value"]])) * 1.1
    max_y = max(pd.concat([power["value"], demand["value"]])) * 1.1
    fig.update_layout(
        yaxis=dict(
            range=[min_y, max_y]
        ),
        yaxis2=dict(
            range=[min_y, max_y]
        )
    )

    st.plotly_chart(fig, config={'displayModeBar': False})

def big_chart_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit):
    # State management
    data_root = set_data_root()

    power = pd.DataFrame()
    store = pd.DataFrame()
    resolution = '1w'

    generators=['solar', 'onwind', 'offwind', 'backstop']
    charge_converters=["battery-charge", "h2-electrolysis"]
    discharge_converters=["battery-discharge", "gas-turbine"]

    for generator in generators:
        power_type = "power_t_" if generator == "backstop" else "power_to_load_t_"
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"{power_type}{resolution}.csv.gz"
        if fname.is_file():
            generator_data = pd.read_csv(fname, compression='gzip', parse_dates=True)
            generator_data = generator_data.rename(columns={generator: 'value'})
            generator_data['type'] = generator
            power = pd.concat([power, generator_data], axis=0)
    for discharger in discharge_converters:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'converters' / discharger / f"power_t_{resolution}.csv.gz"
        if fname.is_file():
            discharger_data = pd.read_csv(fname, compression='gzip', parse_dates=True)
            discharger_data = discharger_data.rename(columns={discharger: 'value'})
            discharger_data['type'] = discharger
            power = pd.concat([power, discharger_data], axis=0)
    '''
    for charger in charge_converters:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'converters' / charger / f"power_t_{resolution}.csv.gz"
        if fname.is_file():
            charger_data = pd.read_csv(fname, compression='gzip', parse_dates=True)
            charger_data = charger_data.rename(columns={charger: 'value'})
            charger_data['type'] = charger
            charger_data['value'] = charger_data['value']
            store = pd.concat([store, charger_data], axis=0)
    '''
    demand = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'demand' / f"demand_t_{resolution}.csv.gz", compression='gzip')
    demand = demand.rename(columns={"timestamp": 'snapshot'})
    demand['type'] = "demand"

    with st.container(border=True):
        st.markdown(f'<p style="font-size:16px;">{TEXTS["Production"]}</p>', unsafe_allow_html=True)
        # _big_chart(power, store, demand) TODO: Removed on request of client
        _big_chart(power, '', demand)
