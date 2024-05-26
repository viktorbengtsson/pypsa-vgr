import streamlit as st
import os.path
from gen_table import render_generators_table
from capacity_chart import render_capacity_chart
from energy_chart import render_energy_chart
from lab import render_network, render_demand
from map_selector import render_map


ROOT = ".."


########## / Streamlit init \ ##########

st.set_page_config(layout="wide")
#st.title('PyPSA-VGR')
col1, col2 = st.columns([2, 1])

st.markdown(
    """
    <style>
        div[class^='block-container'] {
            padding-top: 2.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

########## \ Streamlit init / ##########

########## / State \ ##########
if 'lan' not in st.session_state:
    st.session_state['lan'] = None
if 'kom' not in st.session_state:
    st.session_state['kom'] = None
if 'lan' not in st.query_params:
    st.query_params.lan = None
if 'kom' not in st.query_params:
    st.query_params.kom = None

selected_lan_code = st.query_params.lan
selected_kom_code = st.query_params.kom

if st.session_state.lan is None:
    selected_lan_code = None if st.query_params.lan == "None" else st.query_params.lan
else:
    selected_lan_code = st.session_state.lan
    st.query_params.lan = selected_lan_code

if st.session_state.kom is None:
    selected_kom_code = None if st.query_params.kom == "None" else st.query_params.kom
else:
    selected_kom_code = st.session_state.kom
    st.query_params.kom = selected_kom_code

########## \ State / ##########

with st.sidebar:
    render_map(ROOT, selected_lan_code, selected_kom_code)

########## / Energy info from selection \ ##########

if selected_lan_code:
    selected_year = 2011
    START=f"{str(selected_year)}-01"
    END=f"{str(selected_year)}-12"

    filepattern = f"{ROOT}/data/result/{{}}-{selected_lan_code}-{selected_kom_code}-{START}-{END}.{{}}"

    testfile = filepattern.format("network", "nc")

    if not os.path.isfile(testfile):
        col1.write(f"No files for this selection, missing file: {testfile}")
    else:

        # Filters
        col2.slider("Konstruktion start och slut år", 2020, 2050, (2023, 2026))
        col2.checkbox("Begränsa turbiner?")
        col2.toggle("Vätgas på/av")
        col2.toggle("Biogas på/av")
        col2.slider("Elproduktionsmål", 0.0, 100.0, 75.0, step=(5.0))

        render_generators_table(col1)
        render_capacity_chart(col1, col1)
        render_energy_chart(col2)

        #render_network(col2, filepattern)
        #render_demand(col1)

########## \ Energy info from selection / ##########

