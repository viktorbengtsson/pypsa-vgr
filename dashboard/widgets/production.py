import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
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

def _big_chart(data):
    color_mapping = full_palette()
    fig = px.bar(data, 
        x='snapshot',
        y='value',
        color='generator',
        color_discrete_map=color_mapping
    )

    fig.update_layout(
        height=240,
        barmode='stack',
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        margin=dict(t=0, b=40, l=40, r=40)
    )
    fig.update_xaxes(
        dtick='M1',
        tickformat='%b'
    )
    st.plotly_chart(fig, config={'displayModeBar': False})

def big_chart_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, generators):

    # State management
    data_root = set_data_root()

    generators_data = pd.DataFrame()
    resolution = '1w'

    for generator in generators:
        generator_data = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv", parse_dates=True)
        generator_data = generator_data.rename(columns={generator: 'value'})
        generator_data['generator'] = generator
        generators_data = pd.concat([generators_data, generator_data], axis=0)

    print(generators_data)

    col1, col2 = st.columns([8, 1], gap="small")
    with col1:
        #st.altair_chart(_big_chart(generators_data), use_container_width=True)
        _big_chart(generators_data)

    with col2:
        _legend()
