import streamlit as st
from widgets import render_widgets
from capacity_chart import render_capacity_chart, render_compare_capacity_chart
from energy_chart import render_compare_energy_chart
from legend import render_legend
from data_loading import _config_from_variables, ensure_default_variables, demand_data_from_variables, network_data
#from tab_settings import render_settings
from filters import render_filters, render_filters_compare_mode, filters_update_variables
import paths

CONFIG_NAME = "single"

########## / Streamlit init \ ##########

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
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
        svg[data-testid="stMetricDeltaIcon-Up-OFF"] {
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
if "DATA_ROOT" in st.secrets:
    # Manually set in Community Cloud Secrets to "./data"
    DATA_ROOT = st.secrets["DATA_ROOT"]
    CONFIG_DATA_ROOT = st.secrets["CONFIG_DATA_ROOT"]
else:
    DATA_ROOT = paths.output_path
    CONFIG_DATA_ROOT = paths.config_path

if "clear-cache" in st.query_params and st.query_params["clear-cache"] == "true":
    print("Clearing cache")
    st.query_params["clear-cache"] = "false"
    st.rerun()
    demand_data_from_variables.clear()
    network_data.clear()

selected_lan_code = None if not "geography" in st.query_params or st.query_params.geography == "None" else st.query_params.geography.split(":")[0]
selected_kom_code = None if not "geography" in st.query_params or (st.query_params.geography == "None" or len(st.query_params.geography.split(":")) != 2) else st.query_params.geography.split(":")[1]

def on_click(is_compare_mode, VARIABLES, filters):
    if is_compare_mode:
        del st.session_state.compare_config
    else:
        st.session_state.compare_config = filters_update_variables(DATA_ROOT, CONFIG_NAME, VARIABLES, filters, st.query_params)

########## \ State / ##########

if DEBUG:
    tab1, tab2, tab3, tab4 = st.tabs(["Översikt", "Avancerat", "Lab", "Inställningar"])
    with tab1:
        col2, col1 = st.columns([4, 13], gap="large")
else:
    col2, col1 = st.columns([4, 13], gap="large")

#if DEBUG:
#    render_settings(CONFIG_DATA_ROOT, tab4, CONFIG_NAME)

########## / Energy info from selection \ ##########

if selected_lan_code:
    selected_year = 2011
    is_compare_mode = "compare_config" in st.session_state
    col2A, col2B = col2.columns([1,1]) if is_compare_mode else [col2, col2]

    VARIABLES = ensure_default_variables(st.query_params, CONFIG_DATA_ROOT, CONFIG_NAME)
    if is_compare_mode:
        render_filters_compare_mode(CONFIG_DATA_ROOT, st.session_state.compare_config, col2A, CONFIG_NAME)
    [VARIABLES, compare_button_st_obj, filters] = render_filters(CONFIG_DATA_ROOT, col2B, CONFIG_NAME, VARIABLES, st.query_params, is_compare_mode)

    CONFIG = _config_from_variables(DATA_ROOT, CONFIG_NAME, VARIABLES)
    COMPARE_CONFIG = None

    if CONFIG is None:
        col1.write("Inget scenario har genererats för detta län med dina filter val")
    else:
        if is_compare_mode:
            COMPARE_CONFIG = st.session_state.compare_config
            compare_button_st_obj = col2A
            text = ":x: Stäng jämförelse"
        else:
            text = ":pushpin: Jämför"
        
        compare_button_st_obj.button(text, on_click=lambda: on_click(is_compare_mode, VARIABLES, filters), use_container_width=True)

        if is_compare_mode:
            render_legend(DATA_ROOT, col2A, COMPARE_CONFIG, True)
            render_legend(DATA_ROOT, col2B, CONFIG, False)
            render_compare_energy_chart(DATA_ROOT, col1, CONFIG, COMPARE_CONFIG)
            render_widgets(DATA_ROOT, col1, CONFIG, COMPARE_CONFIG)
            render_compare_capacity_chart(DATA_ROOT, st, CONFIG, COMPARE_CONFIG)
        else:
            render_legend(DATA_ROOT, col2, CONFIG, False)
            render_widgets(DATA_ROOT, col1, CONFIG, None)
            render_capacity_chart(DATA_ROOT, st, CONFIG)

        #if DEBUG:
        #    render_generators_table(DATA_ROOT, tab3, CONFIG)
        #    render_network(tab3, CONFIG)
        #    render_demand(tab3, CONFIG)

else:
    st.write("No selection")

########## \ Energy info from selection / ##########
