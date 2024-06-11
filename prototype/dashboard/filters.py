from data_loading import read_dashboard_available_variables

def render_filters(st_obj, CONFIG_NAME, VARIABLES, var_dict):
    SCENARIOS = read_dashboard_available_variables(CONFIG_NAME)

    has_change = False

    #st_obj.slider("Konstruktion start och slut år", 2020, 2050, (2023, 2026))
    #st_obj.checkbox("Begränsa turbiner?")

    nuclear = st_obj.toggle("Kärnkraft på/av", value=VARIABLES["network_nuclear"])
    h2 = st_obj.toggle("Vätgas på/av", value=VARIABLES["network_h2"])
    biogas = st_obj.selectbox("Biogas", SCENARIOS["network"]["biogas"], index=SCENARIOS["network"]["biogas"].index(VARIABLES["network_biogas"]) if VARIABLES["network_biogas"] in SCENARIOS["network"]["biogas"] else None)

    load_target = st_obj.select_slider("Elproduktionsmål", options=SCENARIOS["load-target"], value=VARIABLES["load_target"])

    if bool(VARIABLES["network_nuclear"]) != bool(nuclear):
        var_dict.network_nuclear = nuclear
        has_change = True
    if bool(VARIABLES["network_h2"]) != bool(h2):
        var_dict.network_h2 = h2
        has_change = True
    if str(VARIABLES["network_biogas"]) != str(biogas):
        var_dict.network_biogas = biogas
        has_change = True
    if int(VARIABLES["load_target"]) != int(load_target):
        var_dict.load_target = load_target
        has_change = True

    return has_change
