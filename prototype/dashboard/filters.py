from data_loading import read_dashboard_available_variables

def render_filters(st_obj, CONFIG_NAME, VARIABLES, var_dict):
    SCENARIOS = read_dashboard_available_variables(CONFIG_NAME)

    if len(SCENARIOS["load-target"]) > 1:
        load_target = st_obj.select_slider("Elproduktionsmål [TWh]", options=SCENARIOS["load-target"], value=VARIABLES["load_target"])
    else:
        load_target = SCENARIOS["load-target"][0]

    nuclear = st_obj.toggle("Kärnkraft", value=(VARIABLES["network_nuclear"] == "True"))
    h2 = st_obj.toggle("Vätgas", value=(VARIABLES["network_h2"] == "True"))
    offwind = st_obj.toggle("Havsvind", value=(VARIABLES["network_offwind"] == "True"))
    #biogas = st_obj.selectbox("Biogas", SCENARIOS["network"]["biogas"], index=SCENARIOS["network"]["biogas"].index(VARIABLES["network_biogas"]) if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else None)
    if len(SCENARIOS["network"]["biogas"]) > 1:
        biogas = st_obj.select_slider("Biogas", options=SCENARIOS["network"]["biogas"], value=VARIABLES["network_biogas"] if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else SCENARIOS["network"]["biogas"][0])
    else:
        biogas = SCENARIOS["network"]["biogas"][0]
    #wind = st_obj.selectbox("Vindkrafts", ["Statisk", "Försiktig", "Aggressiv"], index=0)
    wind = st_obj.select_slider("Vindkrafts", options=["Statisk", "Försiktig", "Aggressiv"], value="Statisk")
    #h2_industry = st_obj.selectbox("Vätgasuttag industri", ["Ingen", "Liten", "Medel", "Stor"], index=0)
    h2_industry = st_obj.select_slider("Vätgasuttag industri", options=["Ingen", "Liten", "Medel", "Stor"], value="Liten")

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

    return VARIABLES
