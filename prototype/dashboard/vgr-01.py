import streamlit as st
import time
from gen_table import render_generators_table
from widgets import render_widgets, render_total_widgets
from capacity_chart import render_capacity_chart, render_compare_capacity_chart
from energy_chart import render_energy_chart, render_compare_energy_chart
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
        div[data-testid="stAppViewBlockContainer"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div:last-of-type {
            margin-top: -2rem;
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
        label[data-baseweb="checkbox"] {
            display: flex;
            flex-direction: row-reverse;
            float: left;
            margin-left: -1.5rem;
        }
        label[data-baseweb="checkbox"] > div {
            margin-left: 1rem;
        }
        label[data-baseweb="checkbox"] > div div[data-testid="stMarkdownContainer"] {
            min-width: 5rem;
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
        button[data-testid="baseButton-secondary"] {
            zoom: 0.9;
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

def on_click(config):
    if "compare_config" in st.session_state:
        del st.session_state.compare_config
    else:
        st.session_state.compare_config = config

########## \ State / ##########

if DEBUG:
    tab1, tab2, tab3, tab4 = st.tabs(["Översikt", "Avancerat", "Lab", "Inställningar"])
    with tab1:
        col2, col1 = st.columns([4, 13], gap="large")
else:
    col2, col1 = st.columns([4, 13], gap="large")

if DEBUG:
    render_settings(tab4, CONFIG_NAME)

########## / Energy info from selection \ ##########

if selected_lan_code:
    selected_year = 2011

    VARIABLES = ensure_default_variables(st.query_params)
    VARIABLES = render_filters(col2, CONFIG_NAME, VARIABLES, st.query_params)

    CONFIG = _config_from_variables(CONFIG_NAME, VARIABLES)
    COMPARE_CONFIG = None
    if "compare_config" in st.session_state:
        COMPARE_CONFIG = st.session_state.compare_config
        if CONFIG["scenario"]["data-path"] == COMPARE_CONFIG["scenario"]["data-path"]:
            COMPARE_CONFIG = None

    if CONFIG is None:
        col1.write("Inget scenario har genererats för detta län med dina filter val")
    else:

        button_col = col2
        if COMPARE_CONFIG is not None:
            col2A, col2B = col2.columns([1,1])
            button_col = col2A
       
        if "compare_config" in st.session_state:
            if COMPARE_CONFIG is None:
                #col2.write("Change selection above")
                text = ":x: Rensa val för jämförelse"
            else:
                text = ":x: Rensa"
        else:
            text = ":pushpin: Välj för jämförelse"
        if button_col.button(text, on_click=lambda: on_click(CONFIG), use_container_width=True):
            if "compare_config" in st.session_state:
                del st.session_state.compare_config
            else:
                st.session_state.compare_config = CONFIG

        if COMPARE_CONFIG is None:
            render_legend(col2, CONFIG, False)
        else:
            col2A, col2B = col2.columns([1,1])
            render_legend(col2A, COMPARE_CONFIG, True)
            render_legend(col2B, CONFIG, False)

        if COMPARE_CONFIG is not None:
            #colA, colB = col1.columns([2,1], gap="medium")
            render_compare_energy_chart(col1, CONFIG, COMPARE_CONFIG)
            #render_total_widgets(colB, CONFIG, COMPARE_CONFIG)


        #tab1, tab2 = col1.tabs(["Elproduktion/konsumption (MWh)", "Elpris"])
        render_widgets(col1, CONFIG, COMPARE_CONFIG)

        #render_generators_table(colA, CONFIG)
        if COMPARE_CONFIG is None:
            render_capacity_chart(st, CONFIG)
        else:
            render_compare_capacity_chart(st, CONFIG, COMPARE_CONFIG)

        #colFoot01, colFoot02, colFoot03, colFoot04, colFoot05, colFoot06 = st.columns([3, 3, 3, 3, 3, 2])
        #colFoot06.image("./qr.png", use_column_width=True)

        if DEBUG:
            render_network(tab3, CONFIG)
            render_demand(tab3, CONFIG)

            render_advanced(tab2, CONFIG)

########## \ Energy info from selection / ##########

