import streamlit as st
import pandas as pd
import altair as alt
from library.config import set_data_root
from widgets.utilities import round_and_prefix, round_and_prettify, scenario
import os.path

# Create the line chart using Altair
def power_line(data, type):
    return alt.Chart(data).mark_line().encode(
        x=alt.X('snapshot:T', title=None),
        y=alt.Y(f"{type}:Q", title=None)
    ).properties(
        height=150  # Set the height of the chart
    ).configure_axis(
        grid=False,  # Remove the grid lines
        domain=False,  # Remove the axis lines
        labels=False,  # Remove the axis labels
        ticks=False  # Remove the axis ticks
    ).configure_view(
        strokeWidth=0  # Remove the border around the chart
    )

def energy_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, generator):
    # State management
    data_root = set_data_root()


    resolution = '1w'
    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv"
    if not os.path.isfile(fname):
        with st.container():
            col1, col2 = st.columns(2)
            col1.metric(label='Nominal effect', value=round_and_prefix(0,'M','W'))
            col2.metric(label='Units required', value=round_and_prettify(0,generator))
        return

    power_t = pd.read_csv(fname, parse_dates=True)
    if resolution == '1w':
        power_t = power_t.iloc[1:]

    details = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / 'details.csv',index_col=0)

    with st.container():
        col1, col2 = st.columns(2)
        col1.metric(label='Nominal effect', value=round_and_prefix(details.loc['p_nom_opt'][generator],'M','W'))
        col2.metric(label='Units required', value=round_and_prettify(details.loc['mod_units'][generator],generator))
        st.altair_chart(power_line(power_t, generator), use_container_width=True)