import streamlit as st
import pandas as pd
import altair as alt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from library.config import set_data_root
from widgets.utilities import scenario, full_palette
from library.language import TEXTS

def _legend():
    color_mapping = full_palette()

    generators = ['solar', 'onwind', 'offwind', 'backstop','biogas_market']
    gen_legends = alt.Chart(None).mark_circle(size=0).encode(
        color=alt.Color('any:N', scale=alt.Scale(
            domain=[TEXTS[key] for key in generators if key in TEXTS],
            range=[color_mapping[key] for key in generators if key in color_mapping])
        ).legend(title=TEXTS["Generator types"], fillColor="#FFFFFF", symbolOpacity=1, symbolType="square", orient='left'),
    ).configure_view(strokeWidth=0
    ).properties( width=100, height=120, title='')

    stores = ['h2', 'battery']
    stor_legends = alt.Chart(None).mark_circle(size=0).encode(
        color=alt.Color('any:N', scale=alt.Scale(
            domain=[TEXTS[key] for key in stores if key in TEXTS],
            range=[color_mapping[key] for key in stores if key in color_mapping])
        ).legend(title=TEXTS["Storage types"], fillColor="#FFFFFF", symbolOpacity=1, symbolType="square", orient='left'),
    ).configure_view(strokeWidth=0
    ).properties( width=100, height=60, title='')

    st.altair_chart(gen_legends, use_container_width=True)
    st.altair_chart(stor_legends, use_container_width=True)

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
            ),
            secondary_y=False
        )
    for type in store['type'].unique():
        filtered_data = store[store['type'] == type]
        if type not in color_mapping:
            raise Exception(f"Cannot find {type} in color mapping")
        fig.add_trace(
            go.Bar(
                x=filtered_data["snapshot"], 
                y=filtered_data["value"], 
                marker_color=color_mapping[type],
                yaxis="y2"
            ),
            secondary_y=True
        )

    fig.add_trace(
        go.Scatter(
            x=demand["snapshot"],
            y=demand["value"],
            name="Demand",
            mode="lines+markers",
            marker_color=color_mapping["demand"]
        ),
        secondary_y=False,
    )

    fig.update_layout(
        height=240,
        barmode='stack',
        showlegend=False,
        yaxis=dict(title=None),
        yaxis2=dict(title=None, overlaying='y', side='right'),  # Secondary y-axis
        margin=dict(t=0, b=40, l=40, r=40)
    )
    fig.update_xaxes(
        dtick='M1',
        tickformat='%b'
    )

    min_y = min(pd.concat([power["value"], store["value"], demand["value"]]))
    max_y = max(pd.concat([power["value"], store["value"], demand["value"]]))
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
    stores=["h2", "battery"]

    for generator in generators:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv"
        if fname.is_file():
            generator_data = pd.read_csv(fname, parse_dates=True)
            generator_data = generator_data.rename(columns={generator: 'value'})
            generator_data['type'] = generator
            power = pd.concat([power, generator_data], axis=0)
    for store_key in stores:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'stores' / store_key / f"power_t_{resolution}.csv"
        print(fname)
        if fname.is_file():
            stores_data = pd.read_csv(fname, parse_dates=True)
            stores_data = stores_data.rename(columns={store_key: 'value'})
            stores_data['type'] = store_key
            store = pd.concat([store, stores_data], axis=0)

    demand = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'demand' / f"demand_t_{resolution}.csv")
    demand = demand.rename(columns={"timestamp": 'snapshot'})
    demand['type'] = "demand"

    col1, col2 = st.columns([8, 1], gap="small")
    with col1:
        _big_chart(power, store, demand)

    with col2:
        _legend()
