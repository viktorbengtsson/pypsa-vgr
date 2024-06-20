import streamlit as st
from map_selector import render_map

########## / Streamlit init \ ##########

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        [data-testid="collapsedControl"] {
            display: none;
        }
        header[data-testid="stHeader"] {
            display: none;
        }
        div[data-testid^="stAppViewBlockContainer"] {
            padding: 0;
            width: 600px;
            position: fixed;
            top: 0;
            left: 0;
        }
        iframe {
            position: fixed;
            top: 0;
        }
        div[data-testid="stImage"] {
            position: fixed;
            z-index: 100;
            bottom: 1rem;
            left: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

########## \ Streamlit init / ##########

########## / State \ ##########

selected_lan_code = None if not "geography" in st.query_params or st.query_params.geography == "None" else st.query_params.geography.split(":")[0]
selected_kom_code = None if not "geography" in st.query_params or (st.query_params.geography == "None" or len(st.query_params.geography.split(":")) != 2) else st.query_params.geography.split(":")[1]

########## \ State / ##########

########## / Energy info from selection \ ##########

render_map(selected_lan_code, selected_kom_code, True)

st.image("./qr.png", use_column_width=False, width=100)
