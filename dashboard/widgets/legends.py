import streamlit as st
import altair as alt
from widgets.utilities import full_palette
from library.language import TEXTS

def _store_legend():
    color_mapping = full_palette()

    stores = ['h2', 'battery']
    stor_legends = alt.Chart(None).mark_circle(size=0).encode(
        color=alt.Color('any:N', scale=alt.Scale(
            domain=[TEXTS[key] for key in stores if key in TEXTS],
            range=[color_mapping[key] for key in stores if key in color_mapping])
        ).legend(title=TEXTS["Stores types"], fillColor="#FFFFFF", titleColor='black', titleFontSize=15, symbolOpacity=1, symbolType="square", orient='left'),
    ).configure_view(strokeWidth=0
    ).properties( width=100, height=60, title='')

    st.altair_chart(stor_legends, use_container_width=True)

def _gen_legend():
    color_mapping = full_palette()

    generators = ['solar', 'onwind', 'offwind', 'backstop','biogas-market']
    gen_legends = alt.Chart(None).mark_circle(size=0).encode(
        color=alt.Color('any:N', scale=alt.Scale(
            domain=[TEXTS[key] for key in generators if key in TEXTS],
            range=[color_mapping[key] for key in generators if key in color_mapping])
        ).legend(title=TEXTS["Generator types"], fillColor="#FFFFFF", titleColor='black', titleFontSize=15, symbolOpacity=1, symbolType="square", orient='left'),
    ).configure_view(strokeWidth=0
    ).properties( width=100, height=120, title='')

    st.altair_chart(gen_legends, use_container_width=True)

def legends():
    with st.container(border=True):
        col1, col2 = st.columns([1,1], gap="small")

        with col1:
            _gen_legend()
        with col2:
            _store_legend()
