from MapSelector.map_selector.map_selector import custom_map_selector
from library.config import read_dashboard_available_variables

def _render_filtering(st_obj, data_root, variables):
    readonly_mode = False

    #is_compare_mode = st_obj.button("Jämför")

   # if is_compare_mode:
   #     render_filters_compare_mode(DATA_ROOT, st.session_state.compare_config, col2A)
   # [VARIABLES, compare_button_st_obj, filters] = render_filters(DATA_ROOT, col2B, VARIABLES, st.query_params, is_compare_mode)

   # CONFIG = _config_from_variables(DATA_ROOT, VARIABLES)
   # COMPARE_CONFIG = None

    SCENARIOS = read_dashboard_available_variables(data_root)

    if len(SCENARIOS["load-target"]) > 1:
        load_target = st_obj.select_slider("Elproduktionsmål [TWh]", options=SCENARIOS["load-target"], value=variables["load_target"], disabled=readonly_mode, key=f"filter_load_target_{readonly_mode}")
    else:
        if SCENARIOS["load-target"][0] != variables["load_target"]:
            st_obj.write("")
            st_obj.write("It seems like you have a /output/config.json file that does not match the data in /output")
            return
        
        load_target = st_obj.select_slider("Elproduktionsmål [TWh]", options=[SCENARIOS["load-target"][0], SCENARIOS["load-target"][0]], value=SCENARIOS["load-target"][0], disabled=readonly_mode, key=f"filter_load_target_{readonly_mode}")

    nuclear = False
    #nuclear = st_obj.toggle("Kärnkraft", value=(VARIABLES["network_nuclear"] == "True"), disabled=readonly_mode, key=f"filter_nuclear_{readonly_mode}")
    h2 = st_obj.toggle("Vätgas", value=(variables["network_h2"] == "True"), disabled=readonly_mode, key=f"filter_h2_{readonly_mode}")
    offwind = st_obj.toggle("Havsvind", value=(variables["network_offwind"] == "True"), disabled=readonly_mode, key=f"filter_offwind_{readonly_mode}")
    #biogas = st_obj.selectbox("Biogas", SCENARIOS["network"]["biogas"], index=SCENARIOS["network"]["biogas"].index(VARIABLES["network_biogas"]) if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else None)
    if len(SCENARIOS["network"]["biogas"]) > 1:
        biogas = st_obj.select_slider("Biogas", options=SCENARIOS["network"]["biogas"], value=variables["network_biogas"] if variables["network_biogas"] in SCENARIOS["network"]["biogas"] else SCENARIOS["network"]["biogas"][0], disabled=readonly_mode, key=f"filter_biogas_{readonly_mode}")
    else:
        biogas = SCENARIOS["network"]["biogas"][0]
    #wind = st_obj.selectbox("Vindkraft", ["Statisk", "Försiktig", "Aggressiv"], index=0)
    #wind = st_obj.select_slider("Vindkraft", options=["Statisk", "Försiktig", "Aggressiv"], value="Statisk", disabled=readonly_mode, key=f"filter_wind_{readonly_mode}")
    #h2_industry = st_obj.selectbox("Vätgasuttag industri", ["Ingen", "Liten", "Medel", "Stor"], index=0)
    #h2_industry = st_obj.select_slider("Vätgasuttag industri", options=["Ingen", "Liten", "Medel", "Stor"], value="Liten", disabled=readonly_mode, key=f"filter_h2_industry_{readonly_mode}")

    variables["load_target"] = load_target
    variables["biogas"] = biogas
    variables["nuclear"] = nuclear
    variables["h2"] = h2
    variables["offwind"] = offwind
    

    return variables

def render_scenario_selector(st_obj, data_root, geography, variables):
    with st_obj:
        result = custom_map_selector(
            default=geography,
        )

        variables = _render_filtering(st_obj, data_root, variables)

    return [result, variables]



