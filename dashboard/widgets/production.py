import streamlit as st
import pandas as pd
import altair as alt
from library.config import set_data_root
from widgets.utilities import round_and_prefix, round_and_prettify, scenario

# Create the line chart using Altair
def big_chart(data):
    return alt.Chart(data).mark_bar().encode(
        x=alt.X('snapshot:T', title=None),
        y=alt.Y('value:Q', title=None, stack=True),
        color=alt.Color('generator:N', legend=alt.Legend(title="Generator Type"))
    )

def big_chart_widget(geo, year, floor, load, h2, offwind, biogas, generators):

    # State management
    data_root = set_data_root()

    generators_data = pd.DataFrame()
    resolution = '1w'

    for generator in generators:
        generator_data = pd.read_csv(data_root / scenario(geo, year, floor, load, h2, offwind, biogas) / 'generators' / generator / f"power_t_{resolution}.csv", parse_dates=True)
        generator_data = generator_data.rename(columns={generator: 'value'})
        generator_data['generator'] = generator
        generators_data = pd.concat([generators_data, generator_data], axis=0)

    print(generators_data)

    st.altair_chart(big_chart(generators_data), use_container_width=True)
