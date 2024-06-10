import streamlit as st
import time
from gen_table import render_generators_table
from capacity_chart import render_capacity_chart
from energy_chart import render_energy_chart
from lab import render_network, render_demand
from map_selector import render_map
from data_loading import _config_from_variables, ensure_default_variables
from tab_settings import render_settings
from filters import render_filters


CONFIG_NAME = "default"

########## / Streamlit init \ ##########

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        div[class^='block-container'] {
            padding-top: 0rem;
        }
        .stTabs {
            z-index: 1000000;
        }
        .stException {
            margin-top: 2em;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

########## \ Streamlit init / ##########

########## / State \ ##########
if 'count' not in st.session_state:
   st.session_state.count = 0

VARIABLES = ensure_default_variables(st.query_params)

st.session_state.count += 1
selected_lan_code = None if st.query_params.geography == "None" else st.query_params.geography.split(":")[0]
selected_kom_code = None if (st.query_params.geography == "None" or len(st.query_params.geography.split(":")) != 2) else st.query_params.geography.split(":")[1]

########## \ State / ##########

with st.sidebar:
    render_map(selected_lan_code, selected_kom_code)

tab1, tab2, tab3, tab4 = st.tabs(["Översikt", "Avancerat", "Lab", "Inställningar"])
with tab1:
   col1, col2 = st.columns([2, 1])

render_settings(tab4, CONFIG_NAME)

########## / Energy info from selection \ ##########

if selected_lan_code:
    selected_year = 2011

    CONFIG = _config_from_variables(CONFIG_NAME, VARIABLES)

    if render_filters(col2, CONFIG_NAME, VARIABLES, st.query_params):
        time.sleep(1) # Bug: https://github.com/streamlit/streamlit/issues/5511
        st.rerun()

    if CONFIG is None:
        col1.write("Inget scenario har genererats för detta län med dina filter val")
    else:
        render_generators_table(col1, CONFIG)
        render_capacity_chart(col1, col1, CONFIG)
        render_energy_chart(col2, CONFIG)

        render_network(col2, CONFIG)
        render_demand(col1, CONFIG)
else:
        col1.write("Välj ett län i kartan")

########## \ Energy info from selection / ##########

