import json

def _read_config_definition(DATA_ROOT):
    fname=f"{DATA_ROOT}/scenarios.json"
    with open(fname, "r") as f:
        CONFIG_DEFINITION = json.load(f)

    return CONFIG_DEFINITION

def all_keys():
    return [
        "load_target",
        "network_nuclear",
        "network_h2",
        "network_offwind",
        "network_biogas",
    ]

def get_default_variables(DATA_ROOT):
    SCENARIOS = _read_config_definition(DATA_ROOT)["scenarios"]

    return {
        "load_target": int(SCENARIOS["load-target"][0]),
        "network_nuclear": SCENARIOS["network"]["nuclear"][0],
        "network_h2": SCENARIOS["network"]["h2"][0],
        "network_offwind": SCENARIOS["network"]["offwind"][0],
        "network_biogas": SCENARIOS["network"]["biogas"][0]
    }

def read_dashboard_available_variables(DATA_ROOT):
    CONFIG_DEFINITION = _read_config_definition(DATA_ROOT)
    
    return CONFIG_DEFINITION["scenarios"]
