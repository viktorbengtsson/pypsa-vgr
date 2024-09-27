import sys
import streamlit as st
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths

def set_app_config():
    st.set_page_config(
        layout="wide"
    )

def set_data_root():
    if "DATA_ROOT" in st.secrets:
        # Manually set in Community Cloud Secrets
        return st.secrets["DATA_ROOT"]
    else:
        return paths.api_path

def clear_cache():
    print("Clearing cache")
    st.query_params["clear-cache"] = "false"
    st.rerun()

import json

def _read_config_definition(DATA_ROOT):
    fname=f"{DATA_ROOT}/scenarios.json"
    with open(fname, "r") as f:
        CONFIG_DEFINITION = json.load(f)

    return CONFIG_DEFINITION

def all_keys():
    return [
        "self-sufficiency",
        "energy-scenario",
        "h2",
        "offwind",
        "biogas-limit",
    ]

def get_default_variables(DATA_ROOT, query_params):
    SCENARIOS = _read_config_definition(DATA_ROOT)["scenarios"]

    defaults = {
        "target_year": int(SCENARIOS["target-year"][0]) if not "target_year" in query_params else int(query_params["target_year"]),
        "self_sufficiency": float(SCENARIOS["self-sufficiency"][0]) if not "self_sufficiency" in query_params else float(query_params["self_sufficiency"]),
        # TODO: Do something more elegant here to select the 0% change or middle scenario
        "energy_scenario": float(SCENARIOS["energy-scenario"][1]) if not "energy_scenario" in query_params else float(query_params["energy_scenario"]),
        "h2": SCENARIOS["h2"][0] if not "h2" in query_params else (query_params["h2"] == "True"),
        "offwind": SCENARIOS["offwind"][0] if not "offwind" in query_params else (query_params["offwind"] == "True"),
        "biogas_limit": float(SCENARIOS["biogas-limit"][1]) if not "biogas_limit" in query_params else float(query_params["biogas_limit"]),
    }

    return defaults

def read_dashboard_available_variables(DATA_ROOT):
    CONFIG_DEFINITION = _read_config_definition(DATA_ROOT)
    
    return CONFIG_DEFINITION["scenarios"]
