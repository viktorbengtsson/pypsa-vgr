import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from library.config import set_data_root
from widgets.utilities import scenario, full_palette
from library.language import TEXTS
import math


def _bar_chart(data):

    fig = px.bar(
        data,
        x='generator',
        y='lcoe',
        text='lcoe_formatted',
        color='color',
        color_discrete_map='identity',
    )

    fig.update_layout(
        height=180,
        xaxis_title=None,
        yaxis_title=None,
        margin=dict(t=0, b=40, l=40, r=40)
    )
    fig.update_annotations(font_size=16, font_color="black", height=60)
    
    #fig.update_traces(textposition='outside', textfont=dict(size=12))
    fig.update_yaxes(dict(
        showgrid=False,
        ticks='',
        showticklabels=False,
        range=[0, math.ceil(max(data["lcoe"]+0.25))]
    ))

    st.markdown(f'<p style="font-size:16px;">{TEXTS["Levelized Cost of Energy"]}</p>', unsafe_allow_html=True)
    st.plotly_chart(fig, config={'displayModeBar': False})

def price_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit):
    # State management
    data_root = set_data_root()

    color_mapping = full_palette()
    data = pd.DataFrame()

    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'price' / "lcoe.csv"
    if fname.is_file():
        data = pd.read_csv(fname, parse_dates=True)
        data.rename(columns={'Unnamed: 0': 'generator'}, inplace=True)
        data["color"] = data["generator"].map(color_mapping)
        data["generator"] = data["generator"].map(TEXTS)
        data["lcoe_formatted"] = data["lcoe"].apply(lambda x: '{0:.2f}'.format(x))
    
    total_energy = sum(data["total_energy"].fillna(0))
    total_cost = sum(data["total_cost"].fillna(0))
    total_lcoe = total_cost / total_energy / 1000
    data.loc[6] = [TEXTS["Overall"], total_energy, total_cost, total_lcoe, None, color_mapping["ON"], '{0:.2f}'.format(total_lcoe)] 

    data["lcoe"].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)

    with st.container(border=True):
        _bar_chart(data)
