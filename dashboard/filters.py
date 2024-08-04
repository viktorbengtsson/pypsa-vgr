from data_loading import read_dashboard_available_variables, _config_from_variables

def _render_filters(DATA_ROOT, st_obj, VARIABLES, readonly_mode):
    SCENARIOS = read_dashboard_available_variables(DATA_ROOT)

    if len(SCENARIOS["load-target"]) > 1:
        load_target = st_obj.select_slider("Elproduktionsmål [TWh]", options=SCENARIOS["load-target"], value=VARIABLES["load_target"], disabled=readonly_mode, key=f"filter_load_target_{readonly_mode}")
    else:
        if SCENARIOS["load-target"][0] != VARIABLES["load_target"]:
            st_obj.write("")
            st_obj.write("It seems like you have a /output/config.json file that does not match the data in /output")
            return
        
        load_target = st_obj.select_slider("Elproduktionsmål [TWh]", options=[SCENARIOS["load-target"][0], SCENARIOS["load-target"][0]], value=SCENARIOS["load-target"][0], disabled=readonly_mode, key=f"filter_load_target_{readonly_mode}")

    nuclear = st_obj.toggle("Kärnkraft", value=(VARIABLES["network_nuclear"] == "True"), disabled=readonly_mode, key=f"filter_nuclear_{readonly_mode}")
    h2 = st_obj.toggle("Vätgas", value=(VARIABLES["network_h2"] == "True"), disabled=readonly_mode, key=f"filter_h2_{readonly_mode}")
    offwind = st_obj.toggle("Havsvind", value=(VARIABLES["network_offwind"] == "True"), disabled=readonly_mode, key=f"filter_offwind_{readonly_mode}")
    #biogas = st_obj.selectbox("Biogas", SCENARIOS["network"]["biogas"], index=SCENARIOS["network"]["biogas"].index(VARIABLES["network_biogas"]) if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else None)
    if len(SCENARIOS["network"]["biogas"]) > 1:
        biogas = st_obj.select_slider("Biogas", options=SCENARIOS["network"]["biogas"], value=VARIABLES["network_biogas"] if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else SCENARIOS["network"]["biogas"][0], disabled=readonly_mode, key=f"filter_biogas_{readonly_mode}")
    else:
        biogas = SCENARIOS["network"]["biogas"][0]
    #wind = st_obj.selectbox("Vindkraft", ["Statisk", "Försiktig", "Aggressiv"], index=0)
    wind = st_obj.select_slider("Vindkraft", options=["Statisk", "Försiktig", "Aggressiv"], value="Statisk", disabled=readonly_mode, key=f"filter_wind_{readonly_mode}")
    #h2_industry = st_obj.selectbox("Vätgasuttag industri", ["Ingen", "Liten", "Medel", "Stor"], index=0)
    h2_industry = st_obj.select_slider("Vätgasuttag industri", options=["Ingen", "Liten", "Medel", "Stor"], value="Liten", disabled=readonly_mode, key=f"filter_h2_industry_{readonly_mode}")

    return [nuclear, h2, offwind, biogas, load_target]

def _update_variables(VARIABLES, var_dict, filters):
    [nuclear, h2, offwind, biogas, load_target] = filters

    if (VARIABLES["network_nuclear"] == "True") != nuclear:
        var_dict.network_nuclear = nuclear
        VARIABLES["network_nuclear"] = nuclear

    if (VARIABLES["network_h2"] == "True") != h2:
        var_dict.network_h2 = str(h2)
        VARIABLES["network_h2"] = h2
    if (VARIABLES["network_offwind"] == "True") != offwind:
        var_dict.network_offwind = str(offwind)
        VARIABLES["network_offwind"] = offwind
    if str(VARIABLES["network_biogas"]) != str(biogas):
        var_dict.network_biogas = biogas
        VARIABLES["network_biogas"] = biogas
    if int(VARIABLES["load_target"]) != int(load_target):
        var_dict.load_target = load_target
        VARIABLES["load_target"] = load_target

def _if_boolean_then_string(variable):
    if isinstance(variable, bool):
        return str(variable)
    return variable

def render_filters_compare_mode(DATA_ROOT, CONFIG, st_obj):
    VARIABLES = {key.replace('-', '_'): _if_boolean_then_string(value) for key, value in CONFIG["scenario"].items()}
    _render_filters(DATA_ROOT, st_obj, VARIABLES, True)

def render_filters(DATA_ROOT, st_obj, VARIABLES, var_dict, readonly_mode):
    filters = _render_filters(DATA_ROOT, st_obj, VARIABLES, False)

    colA, colB = [st_obj, st_obj] if readonly_mode else st_obj.columns([1,1])
    if colB.button("⟳ Uppdatera", use_container_width=True):
        _update_variables(VARIABLES, var_dict, filters)

    return [VARIABLES, colA, filters]

def filters_update_variables(DATA_ROOT, VARIABLES, filters, var_dict):
    _update_variables(VARIABLES, var_dict, filters)

    return _config_from_variables(DATA_ROOT, VARIABLES)
