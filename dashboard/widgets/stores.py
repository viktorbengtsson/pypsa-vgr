import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from library.config import set_data_root
from widgets.utilities import scenario, full_palette
from library.language import TEXTS

def _pie_chart(data):

    filtered_data = data[(data["value_type"] == "e_nom_opt") & (data["value"] > 0)]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=filtered_data["label"],
                values=filtered_data["value"],
                marker=dict(colors=filtered_data["color"]),
                textinfo='label+percent'
            )
        ]
    )

    fig.update_layout(
        height=240,
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(t=80, b=40, l=40, r=40)
    )

    st.plotly_chart(fig, config={'displayModeBar': False})

def _bar_chart(data):

    filtered_data = data[(data["value_type"] == "e_nom_opt") & (data["value"] > 0)]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=filtered_data['value'],
            y=filtered_data['label'],
            marker=dict(color=filtered_data['color']),
            orientation='h'
        )
    )

    fig.update_layout(
        barmode='stack',
        height=156,
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(t=0, b=40, l=40, r=40)  # Set the margins
    )

    st.plotly_chart(fig, config={'displayModeBar': False})

def stores_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit):
    # State management
    data_root = set_data_root()

    color_mapping = full_palette()
    data = pd.DataFrame()
    stores=["h2", "battery"]

    for store_key in stores:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'stores' / store_key / "details.csv"
        if fname.is_file():
            stores_data = pd.read_csv(fname, parse_dates=True)
            stores_data.rename(columns={'Unnamed: 0': 'value_type'}, inplace=True)
            stores_data = stores_data.rename(columns={store_key: 'value'})
            stores_data['type'] = store_key
            stores_data['label'] = TEXTS[store_key]
            stores_data['color'] = color_mapping[store_key]
            data = pd.concat([data, stores_data], axis=0)

    with st.container(border=True):
        st.markdown(f'<p style="font-size:16px;">{TEXTS["Store capacity"]}</p>', unsafe_allow_html=True)
        _bar_chart(data)
