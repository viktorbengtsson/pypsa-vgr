from data_loading import read_dashboard_available_variables

def render_filters(st_obj, CONFIG_NAME, VARIABLES, var_dict):
    SCENARIOS = read_dashboard_available_variables(CONFIG_NAME)

    if len(SCENARIOS["load-target"]) > 1:
        load_target = st_obj.select_slider("Elproduktionsmål [TW]", options=SCENARIOS["load-target"], value=VARIABLES["load_target"])
    else:
        load_target = SCENARIOS["load-target"][0]

    nuclear = st_obj.toggle("Kärnkraft på/av", value=(VARIABLES["network_nuclear"] == "True"))
    h2 = st_obj.toggle("Vätgas på/av", value=(VARIABLES["network_h2"] == "True"))
    offwind = st_obj.toggle("Havsvind på/av", value=True)
    biogas = st_obj.selectbox("Biogas scenario", SCENARIOS["network"]["biogas"], index=SCENARIOS["network"]["biogas"].index(VARIABLES["network_biogas"]) if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else None)
    wind = st_obj.selectbox("Vindkrafts scenario", ["Statisk", "Försiktig", "Aggresiv"], index=0)
    h2_industry = st_obj.selectbox("Vätgas till industri", ["Liten", "Medel", "Stor"], index=0)

    if (VARIABLES["network_nuclear"] == "True") != nuclear:
        var_dict.network_nuclear = nuclear
        VARIABLES["network_nuclear"] = nuclear

    if (VARIABLES["network_h2"] == "True") != h2:
        var_dict.network_h2 = str(h2)
        VARIABLES["network_h2"] = h2
    if str(VARIABLES["network_biogas"]) != str(biogas):
        var_dict.network_biogas = biogas
        VARIABLES["network_biogas"] = biogas
    if int(VARIABLES["load_target"]) != int(load_target):
        var_dict.load_target = load_target
        VARIABLES["load_target"] = load_target

    return VARIABLES
