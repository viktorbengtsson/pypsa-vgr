import streamlit as st
from library.config import set_data_root, read_dashboard_available_variables
from library.language import TEXTS

def _is_loaded(key):
    st.session_state[f"is_loaded_{key}"] = True

def controls_widget(variables):
    # State management
    data_root = set_data_root()

    SCENARIOS = read_dashboard_available_variables(data_root)

    # LOAD TARGET
    load_target_title = f'{TEXTS["Production target"]} [TWh]'
    if len(SCENARIOS["load-target"]) > 1:
        if 'is_loaded_load_target' not in st.session_state:
            load_target = st.select_slider(load_target_title, options=SCENARIOS["load-target"], value=variables["load_target"], on_change=lambda: _is_loaded("load_target"))
        else:
            load_target = st.select_slider(load_target_title, options=SCENARIOS["load-target"])
    else:
        if SCENARIOS["load-target"][0] != variables["load_target"]:
            st.write("")
            st.write("It seems like you have a /output/config.json file that does not match the data in /output")
            return
        
        if 'is_loaded_load_target' not in st.session_state:
            load_target = st.select_slider(load_target_title, options=[SCENARIOS["load-target"][0], SCENARIOS["load-target"][0]], value=SCENARIOS["load-target"][0], on_change=lambda: _is_loaded("load_target"))
        else:
            load_target = st.select_slider(load_target_title, options=[SCENARIOS["load-target"][0], SCENARIOS["load-target"][0]])

    # H2
    if 'is_loaded_h2' not in st.session_state:
        h2 = st.toggle(TEXTS["h2"], value=variables["h2"], disabled=(len(SCENARIOS["h2"]) == 1), on_change=lambda: _is_loaded("h2"))
    else:
       h2 = st.toggle(TEXTS["h2"], disabled=(len(SCENARIOS["h2"]) == 1))
    
    # OFFWIND
    if 'is_loaded_offwind' not in st.session_state:
        offwind = st.toggle(TEXTS["Offshore"], value=(variables["offwind"]), disabled=(len(SCENARIOS["offwind"]) == 1), on_change=lambda: _is_loaded("offwind"))
    else:
        offwind = st.toggle(TEXTS["Offshore"], disabled=(len(SCENARIOS["offwind"]) == 1))

    # BIOGAS
    if len(SCENARIOS["biogas-limit"]) > 1:
        if 'is_loaded_biogas' not in st.session_state:
            biogas = st.select_slider(TEXTS["Biogas"], options=SCENARIOS["biogas-limit"], value=variables["biogas_limit"] if variables["biogas_limit"] in SCENARIOS["biogas-limit"] else SCENARIOS["biogas-limit"][0], on_change=lambda: _is_loaded("biogas"))
        else:
            biogas = st.select_slider(TEXTS["Biogas"], options=SCENARIOS["biogas-limit"])
    else:
        biogas = SCENARIOS["biogas-limit"][0]

    variables["target_year"] = 2035 # Controls for this?
    variables["floor"] = 0.5 # Controls for this?
    variables["load_target"] = load_target
    variables["h2"] = h2
    variables["offwind"] = offwind
    variables["biogas_limit"] = biogas

    return variables

def controls_readonly_widget(variables):
    # State management
    data_root = set_data_root()

    SCENARIOS = read_dashboard_available_variables(data_root)

    # LOAD TARGET
    if len(SCENARIOS["load-target"]) > 1:
        st.select_slider("", options=SCENARIOS["load-target"], value=variables["load_target"], disabled=True, label_visibility="hidden", key="readonly_load_target")
    else:
        st.select_slider("", options=[variables["load_target"], variables["load_target"]], value=variables["load_target"], disabled=True, label_visibility="hidden", key="readonly_load_target")

    # H2
    st.toggle("", value=(variables["h2"]), disabled=True, label_visibility="hidden", key="readonly_h2")

    # OFFWIND
    st.toggle("", value=(variables["offwind"]), disabled=True, label_visibility="hidden", key="readonly_offwind")

    # BIOGAS
    if len(SCENARIOS["biogas-limit"]) > 1:
        st.select_slider("", options=[variables["biogas_limit"], variables["biogas_limit"]], disabled=True, label_visibility="hidden", key="readonly_biogas")
