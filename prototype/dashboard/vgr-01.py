import streamlit as st
import time
from gen_table import render_generators_table
from widgets import render_widgets
from capacity_chart import render_capacity_chart, render_monthly_capacity_chart
from energy_chart import render_energy_chart
from legend import render_legend
from lab import render_network, render_demand
from data_loading import _config_from_variables, ensure_default_variables
from tab_settings import render_settings
from advanced import render_advanced
from filters import render_filters

CONFIG_NAME = "default"

########## / Streamlit init \ ##########

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        [data-testid="collapsedControl"] {
            display: none;
        }
        div[class^='block-container'] {
            padding-top: 1rem;
            padding-left: 3rem;
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
        div[data-baseweb="select"] > div {
            background-color: transparent;
        }
        div[data-baseweb="select"] > div > div {
            padding: 0.25rem 0.35rem 0.0rem 0.35rem;
        }
        div[data-baseweb="popover"] li {
            font-size: 0.85rem;
        }
        .stDeployButton {
            display: none;
        }
        svg[data-testid="stMetricDeltaIcon-Up"] {
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

if selected_lan_code:
    selected_year = 2011

    VARIABLES = ensure_default_variables(st.query_params)
    VARIABLES = render_filters(col2, CONFIG_NAME, VARIABLES, st.query_params)

    CONFIG = _config_from_variables(CONFIG_NAME, VARIABLES)

    if CONFIG is None:
        col1.write("Inget scenario har genererats för detta län med dina filter val")
    else:
        render_legend(col2, CONFIG)
        #tab1, tab2 = col1.tabs(["Elproduktion/konsumption (MWh)", "Elpris"])
        render_capacity_chart(col1, CONFIG)
        #render_monthly_capacity_chart(col1, CONFIG)

        #st.write("")
        #colA, colB = st.columns([2, 1])
       
        col2.write("")
        col2.write("")
        col2.write("")
        col2.write("")
        col2.write("")
        col2.write("")
        render_energy_chart(col2, CONFIG)
        #render_generators_table(colA, CONFIG)
        render_widgets(col1, CONFIG)

        #colFoot01, colFoot02, colFoot03, colFoot04, colFoot05, colFoot06 = st.columns([3, 3, 3, 3, 3, 2])
        #colFoot06.image("./qr.png", use_column_width=True)

        if DEBUG:
            render_network(tab3, CONFIG)
            render_demand(tab3, CONFIG)

            render_advanced(tab2, CONFIG)

########## \ Energy info from selection / ##########

