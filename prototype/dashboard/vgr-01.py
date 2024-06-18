import streamlit as st
import time
from gen_table import render_generators_table
from capacity_chart import render_capacity_chart
from energy_chart import render_energy_chart
from lab import render_network, render_demand
from map_selector import render_map
from data_loading import _config_from_variables, ensure_default_variables
from tab_settings import render_settings
from advanced import render_advanced
from filters import render_filters

print("Rendering...XX")

CONFIG_NAME = "full"
do_movie = True

########## / Streamlit init \ ##########

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        div[class^='block-container'] {
            padding-top: 1rem;
            padding-left: 6rem;
            padding-bottom: 2rem;
        }
        .element-container-OFF {
            transition: none !important;
        }
        .stTabs {
            z-index: 1000000;
        }
        header[data-testid="stHeader"] {
            background: transparent;
        }
        .stException {
            margin-top: 2em;
        }
        div[data-baseweb="select"] {
            font-size: 0.85rem;
        }
        div[data-baseweb="select"] > div > div {
            padding: 0.5rem 0.35rem 0.25rem 0.35rem;
        }
        div[data-baseweb="popover"] li {
            font-size: 0.85rem;
        }
        .stDeployButton {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

########## \ Streamlit init / ##########

########## / State \ ##########

DEBUG = ("debug" in st.query_params and st.query_params.debug == "True")

selected_lan_code = None if not "geography" in st.query_params or st.query_params.geography == "None" else st.query_params.geography.split(":")[0]
selected_kom_code = None if not "geography" in st.query_params or (st.query_params.geography == "None" or len(st.query_params.geography.split(":")) != 2) else st.query_params.geography.split(":")[1]

########## \ State / ##########

if DEBUG:
    tab1, tab2, tab3, tab4 = st.tabs(["Översikt", "Avancerat", "Lab", "Inställningar"])
    with tab1:
        col2, col1 = st.columns([1, 4], gap="large")
else:
    col2, col1 = st.columns([1, 4], gap="large")

if DEBUG:
    render_settings(tab4, CONFIG_NAME)

########## / Energy info from selection \ ##########

with st.sidebar:
    render_map(selected_lan_code, selected_kom_code, do_movie)


if selected_lan_code:
    selected_year = 2011

    VARIABLES = ensure_default_variables(st.query_params)
    VARIABLES = render_filters(col2, CONFIG_NAME, VARIABLES, st.query_params)

    CONFIG = _config_from_variables(CONFIG_NAME, VARIABLES)

    if CONFIG is None:
        col1.write("Inget scenario har genererats för detta län med dina filter val")
    else:
        render_capacity_chart(col1, col1, CONFIG)

        st.write("")
        colA, colB = st.columns([2, 1])
       
        render_energy_chart(colB, CONFIG)
        render_generators_table(colA, CONFIG)

        colFoot01, colFoot02, colFoot03, colFoot04, colFoot05, colFoot06 = st.columns([3, 3, 3, 3, 3, 2])
        colFoot06.image("./qr.png", use_column_width=True)

        if DEBUG:
            render_network(tab3, CONFIG)
            render_demand(tab3, CONFIG)

            render_advanced(tab2, CONFIG)

########## \ Energy info from selection / ##########

