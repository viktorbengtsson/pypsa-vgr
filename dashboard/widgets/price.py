import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
#from library.config import set_data_root
from library.api import file_exists, read_csv
from widgets.utilities import scenario, full_palette, round_and_prefix
from library.language import TEXTS
import math


def _bar_chart(data):

    total_value = data['lcoe_adjusted'].sum()
    color_mapping = full_palette()

    fig = px.bar(
        data,
        x='lcoe_adjusted',
        y=['']*len(data),
        color='color',
        color_discrete_map='identity',
        opacity=color_mapping['opacity'],
        custom_data=[data['generator_formatted'], data['lcoe']*100, data['total_energy_formatted'], data['total_cost_formatted']],
        orientation='h',
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "" + TEXTS["electricity price"] + ": %{customdata[1]:.0f} " + TEXTS["electricity price unit"] + "<br>"  # lcoe per energy type
            "" + TEXTS["total_energy"] + ": %{customdata[2]}<br>"
            "" + TEXTS["total_cost"] + ": %{customdata[3]}<br>"  # total_cost (formatted with commas and no decimals)
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=140,
        xaxis_title=None,
        yaxis_title=None,
        margin=dict(t=0, b=20, l=10, r=10),
        barmode='stack',
    )
    fig.update_annotations(font_size=16, font_color="black", height=60)

    fig.update_xaxes(dict(
        showticklabels=False,  # Hide x-axis labels
        showgrid=False,        # Hide gridlines
        ticks=''               # Hide ticks
    ))

    fig.update_yaxes(
        showticklabels=False,
        ticks=''
    )

    fig.add_annotation(
        x=total_value,  # Position it at the total value on the x-axis
        y=0,  # Since it's a single bar, position it at y=0
        text=f'{total_value*100:.0f} {TEXTS["electricity price unit"]}',  # The label text showing the total
        showarrow=False,  # No arrow, just the text
        xanchor="left",  # Align the text to the left of the position
        font=dict(size=14, color="black"),  # Customize the font size and color
        xshift=10  # Add some padding between the bar and the label
    )

    st.plotly_chart(fig, config={'displayModeBar': False})

def price_widget(geo, target_year, self_sufficiency, energy_scenario, h2, offwind, biogas_limit, modal):
    # State management
    #data_root = set_data_root()

    color_mapping = full_palette()
    data = pd.DataFrame()

    #fname = data_root / scenario(geo, target_year, self_sufficiency, energy_scenario, h2, offwind, biogas_limit) / 'price' / "lcoe.csv.gz"
    fpath = f"{scenario(geo, target_year, self_sufficiency, energy_scenario, h2, offwind, biogas_limit)}/price/lcoe.csv.gz"
    if file_exists(fpath):
        data = read_csv(fpath, compression='gzip', parse_dates=True)
        data.rename(columns={'Unnamed: 0': 'generator'}, inplace=True)
        data["color"] = data["generator"].map(color_mapping)
    
    total_energy = sum(data["total_energy"].fillna(0))
    total_cost = sum(data["total_cost"].fillna(0))
    total_lcoe = total_cost / total_energy / 1000

    data['lcoe_adjusted'] = data['total_cost'] / total_cost * total_lcoe
    data['generator_formatted'] = data['generator'].apply(lambda x: TEXTS[x])
    data['total_energy_formatted'] = data['total_energy'].apply(lambda x: round_and_prefix(x, 'M', 'Wh', 1))
    data['total_cost_formatted'] = data['total_cost'].apply(lambda x: round_and_prefix(x, '', TEXTS["currency"], 0))
    
    data["lcoe"].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)

    with st.container(border=True):
        st.markdown(f'<p style="font-size:16px;">{TEXTS["LCOE"]}</p>', unsafe_allow_html=True)

        _bar_chart(data)

        if st.button(":material/help:", key='price'):
            modal('price')
