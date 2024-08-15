import streamlit as st
from library.config import set_data_root, read_dashboard_available_variables

def controls_widget(variables):
    # State management
    data_root = set_data_root()

    readonly_mode = False
    SCENARIOS = read_dashboard_available_variables(data_root)

    # LOAD TARGET
    if len(SCENARIOS["load-target"]) > 1:
        load_target = st.select_slider("Elproduktionsmål [TWh]", options=SCENARIOS["load-target"], value=variables["load_target"], disabled=readonly_mode, key=f"filter_load_target_{readonly_mode}")
    else:
        if SCENARIOS["load-target"][0] != variables["load_target"]:
            st.write("")
            st.write("It seems like you have a /output/config.json file that does not match the data in /output")
            return
        
        load_target = st.select_slider("Elproduktionsmål [TWh]", options=[SCENARIOS["load-target"][0], SCENARIOS["load-target"][0]], value=SCENARIOS["load-target"][0], disabled=readonly_mode, key=f"filter_load_target_{readonly_mode}")

    # H2
    h2 = st.toggle("Vätgas", value=(variables["h2"]), disabled=(readonly_mode or len(SCENARIOS["h2"]) == 1), key=f"filter_h2_{readonly_mode}")
    
    # OFF WIND
    offwind = st.toggle("Havsvind", value=(variables["offwind"]), disabled=(readonly_mode or len(SCENARIOS["offwind"]) == 1), key=f"filter_offwind_{readonly_mode}")

    # BIOGAS
    if len(SCENARIOS["biogas-limit"]) > 1:
        biogas = st.select_slider("Biogas", options=SCENARIOS["biogas-limit"], value=variables["biogas_limit"] if variables["biogas_limit"] in SCENARIOS["biogas-limit"] else SCENARIOS["biogas-limit"][0], disabled=readonly_mode, key=f"filter_biogas_{readonly_mode}")
    else:
        biogas = SCENARIOS["biogas-limit"][0]

    variables["target_year"] = 2035 # Controls for this?
    variables["floor"] = 0.5 # Controls for this?
    variables["load_target"] = load_target
    variables["h2"] = h2
    variables["offwind"] = offwind
    variables["biogas_limit"] = biogas

    return variables
