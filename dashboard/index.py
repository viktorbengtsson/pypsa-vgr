import sys
import streamlit as st
from visualizations import render_visualizations
from scenarios import render_scenario_selector
from library.config import get_default_variables
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

import paths

########## / Streamlit init \ ##########
st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="PyPSA-VGR 2035"
)

st.markdown(
    f"""
    <style>
        body, html {{
            margin: 0;
            padding: 0;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

########## \ Streamlit init / ##########

########## / State \ ##########

if "DATA_ROOT" in st.secrets:
    # Manually set in Community Cloud Secrets
    data_root = st.secrets["DATA_ROOT"]
else:
    data_root = paths.output_path

if "clear-cache" in st.query_params and st.query_params["clear-cache"] == "true":
    print("Clearing cache")
    st.query_params["clear-cache"] = "false"
    st.rerun()

if 'geography' not in st.session_state:
    st.session_state['geography'] = [] if not "geography" in st.query_params or st.query_params.geography is None or st.query_params.geography == "" else st.query_params.geography.split(",")
if 'variables' not in st.session_state:
    st.session_state['variables'] = get_default_variables(data_root)

geography = st.session_state['geography']
variables = st.session_state['variables']

########## \ State / ##########


[geography, variables] = render_scenario_selector(st.sidebar, data_root, geography, variables)

col1, col2 = st.columns([3, 1], gap="large")

render_visualizations(col1, col2, data_root, geography, variables)

# Also store session value in query string
st.query_params["geography"] = ','.join(map(str, geography))
