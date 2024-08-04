import json
import pickle
import os
import os.path
import pandas as pd
import streamlit as st

def _read_config_definition(DATA_ROOT):
    fname=f"{DATA_ROOT}/config.json"
    with open(fname, "r") as f:
        CONFIG_DEFINITION = json.load(f)

    return CONFIG_DEFINITION

def _read_constants():
    fname = "./constants.pkl"
    if not os.path.isfile(fname):
        with open(fname, "wb") as f:
            pickle.dump({
                "base_year": 2024,
                "target_year": 2035,
                "discount_rate": 0.05,
                "demand": 2023
            }, f)
    
    with open(fname, "rb") as f:
        CONSTANTS = pickle.load(f)
    
    return CONSTANTS

def _update_constants(code, value):
    CONSTANTS = _read_constants()
    CONSTANTS[code] = value
    fname = "./constants.pkl"
    with open(fname, "wb") as f:
        pickle.dump(CONSTANTS, f)

def _get_scenario_key(CONSTANTS, VARIABLES):
    base_year = CONSTANTS["base_year"]
    target_year = CONSTANTS["target_year"]
    discount_rate = CONSTANTS["discount_rate"]
    demand_data_year = CONSTANTS["demand"]

    load_target = VARIABLES.get("load_target") or 10
    network_nuclear = VARIABLES.get("network_nuclear") or False
    network_h2 = VARIABLES.get("network_h2") or False
    network_offwind = VARIABLES.get("network_offwind") or False
    network_biogas = VARIABLES.get("network_biogas") or "Liten"
    network_onwind_limit = VARIABLES.get("network_onwind_limit")
    network_offwind_limit = VARIABLES.get("network_offwind_limit")
    geography = VARIABLES.get("geography") or "14"

    return f"base-year={base_year},\
target-year={target_year},\
discount-rate={discount_rate},\
demand={demand_data_year},\
load-target={load_target},\
network-nuclear={network_nuclear},\
network-h2={network_h2},\
network-offwind={network_offwind},\
network-biogas={network_biogas},\
network-onwind-limit={network_onwind_limit},\
network-offwind-limit={network_offwind_limit},\
geography={geography}"

def _config_from_variables(DATA_ROOT, VARIABLES):

    CONSTANTS = _read_constants()
    SCENARIO = _get_scenario_key(CONSTANTS, VARIABLES)

    fname = f"{DATA_ROOT}/config/{SCENARIO}/config.json"
    if not os.path.isfile(fname):
        print(f"Could not find file: {fname}")
        return None

    with open(fname, "r") as f:
        CONFIG = json.load(f)

    return CONFIG

def read_dashboard_available_variables(DATA_ROOT):
    CONFIG_DEFINITION = _read_config_definition(DATA_ROOT)
    
    return CONFIG_DEFINITION["scenarios"]

def get_assumption_data(DATA_ROOT):
    return pd.read_csv(f"{DATA_ROOT}/assumptions.csv")

@st.cache_data
def demand_data_from_variables(DATA_ROOT, CONFIG):
    # Setting variables based on config
    YEAR=CONFIG["scenario"]["demand"]
    TARGET=CONFIG["scenario"]["load-target"]
    #DEMAND_KEY = f"{YEAR}/{TARGET}"
    DEMAND_KEY = f"{TARGET}"

    return pd.read_csv(f"{DATA_ROOT}/demand/{DEMAND_KEY}/demand.csv", index_col=1, parse_dates=[1])

@st.cache_data
def network_data(DATA_ROOT, CONFIG, key):
    # Setting variables based on config
    DATA_PATH=CONFIG["scenario"]["data-path"]

    fname = f"{DATA_ROOT}/network/{DATA_PATH}/network_{key}.csv"
    index_col = 0
    if key.endswith("series"):
        df = pd.read_csv(fname, usecols=['keys', 'labels'])
        dict = df.set_index("keys")["labels"].to_dict()
        return dict
    if key == "widgets":
        df = pd.read_csv(fname, index_col=0)
        generators = df[df['widget'] == 'generators'].drop(columns=['widget','key','value'])
        stores = df[df['widget'] == 'stores'].drop(columns=['widget','key','value'])
        biogas_price = None
        backstop = df[df['widget'] == 'backstop']
        backstop_total = backstop[backstop['key'] == 'total']["value"].tolist()[0]
        backstop_fraction = backstop[backstop['key'] == 'fraction']["value"].tolist()[0]
        curtailment = df[df['widget'] == 'curtailment']
        curtailment_total = curtailment[curtailment['key'] == 'total']["value"].tolist()[0]
        curtailment_fraction = curtailment[curtailment['key'] == 'fraction']["value"].tolist()[0]
        return [generators, stores, biogas_price, backstop_total, backstop_fraction, curtailment_total, curtailment_fraction]

    return pd.read_csv(fname, index_col=index_col, parse_dates=[0])

def ensure_default_variables(var_dict, DATA_ROOT):
    SCENARIOS = read_dashboard_available_variables(DATA_ROOT)

    if "load_target" not in var_dict:
        var_dict.load_target = SCENARIOS["load-target"][0]
    if "network_nuclear" not in var_dict:
        var_dict.network_nuclear = SCENARIOS["network"]["nuclear"][0]
    if "network_h2" not in var_dict:
        var_dict.network_h2 = SCENARIOS["network"]["h2"][0]
    if "network_offwind" not in var_dict:
        var_dict.network_offwind = SCENARIOS["network"]["offwind"][0]
    if "network_biogas" not in var_dict:
        var_dict.network_biogas = SCENARIOS["network"]["biogas"][0]
    if "network_onwind_limit" not in var_dict:
        var_dict.network_onwind_limit = None
    if "network_offwind_limit" not in var_dict:
        var_dict.network_offwind_limit = None
    if "geography" not in var_dict:
        var_dict.geography = "14"

    return {
        "geography": var_dict.get("geography"),
        "load_target": int(var_dict.get("load_target")),
        "network_nuclear": var_dict.get("network_nuclear"),
        "network_h2": var_dict.get("network_h2"),
        "network_offwind": var_dict.get("network_offwind"),
        "network_biogas": var_dict.get("network_biogas"),
        "network_onwind_limit": var_dict.get("network_onwind_limit"),
        "network_offwind_limit": var_dict.get("network_offwind_limit"),
    }
