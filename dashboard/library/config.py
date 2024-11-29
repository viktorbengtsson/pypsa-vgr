import streamlit as st
from .api import read_json

def set_app_config():
    st.set_page_config(
        layout="wide"
    )

# In the current backend model offwind generation and h2 storage never get included due to their high price-points and lack of constraints enforcing their use
# We still include them in the frontend since with updated/other prices they are relevant
# TODO: fix this so that the frontend generates based on whether there is any electricity in these generators/stores
include_offwind_and_h2 = False

def clear_cache():
    print("Clearing cache")
    st.query_params["clear-cache"] = "false"
    st.rerun()

def all_keys():
    return [
        "self-sufficiency",
        "energy-scenario",
        "h2",
        "offwind",
        "biogas-limit",
    ]

def get_default_variables(query_params):
    SCENARIOS = read_json('scenarios.json')["scenarios"]

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

def read_dashboard_available_variables():
    return read_json('scenarios.json')['scenarios']
