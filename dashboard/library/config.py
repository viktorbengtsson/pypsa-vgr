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
        return paths.output_path

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
        "load_target",
        "h2",
        "offwind",
        "biogas-limit",
    ]

def get_default_variables(DATA_ROOT):
    SCENARIOS = _read_config_definition(DATA_ROOT)["scenarios"]

    return {
        "load_target": int(SCENARIOS["load-target"][0]),
        "network_h2": SCENARIOS["h2"][0],
        "network_offwind": SCENARIOS["offwind"][0],
        "network_biogas": int(SCENARIOS["biogas-limit"][0])
    }

def read_dashboard_available_variables(DATA_ROOT):
    CONFIG_DEFINITION = _read_config_definition(DATA_ROOT)
    
    return CONFIG_DEFINITION["scenarios"]
