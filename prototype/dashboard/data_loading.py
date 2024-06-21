import streamlit as st
import json
import pickle
import os.path
import pandas as pd
import geopandas as gpd
import pypsa
import atlite
import geopandas as gpd
import pandas as pd
import xarray as xr

def _read_config_definition(CONFIG_NAME):
    fname=f"../configs/{CONFIG_NAME}.json"
    with open(fname, "r") as f:
        CONFIG_DEFINITION = json.load(f)
    
    return CONFIG_DEFINITION

def _read_constants(CONFIG_NAME):
    fname = "./constants.pkl"
    if not os.path.isfile(fname):
        with open(fname, "wb") as f:
            pickle.dump({
                "weather": 2023,
                "costs": 2050,
                "demand": 2025
            }, f)
    
    with open(fname, "rb") as f:
        CONSTANTS = pickle.load(f)
    
    return CONSTANTS

def _update_constants(CONFIG_NAME, code, value):
    CONSTANTS = _read_constants(CONFIG_NAME)
    CONSTANTS[code] = value
    fname = "./constants.pkl"
    with open(fname, "wb") as f:
        pickle.dump(CONSTANTS, f)

def _get_scenario_key(CONSTANTS, VARIABLES):
    weather_data_year = CONSTANTS["weather"]
    costs_data_year = CONSTANTS["costs"]
    demand_data_year = CONSTANTS["demand"]

    load_target = VARIABLES.get("load_target") or 10
    network_nuclear = VARIABLES.get("network_nuclear") or False
    network_h2 = VARIABLES.get("network_h2") or False
    network_offwind = VARIABLES.get("network_offwind") or False
    network_biogas = VARIABLES.get("network_biogas") or "Liten"
    network_onwind_limit = VARIABLES.get("network_onwind_limit")
    network_offwind_limit = VARIABLES.get("network_offwind_limit")
    geography = VARIABLES.get("geography") or "14"

    return f"weather={weather_data_year},\
costs={costs_data_year},\
demand={demand_data_year},\
load-target={load_target},\
network-nuclear={network_nuclear},\
network-h2={network_h2},\
network-offwind={network_offwind},\
network-biogas={network_biogas},\
network-onwind-limit={network_onwind_limit},\
network-offwind-limit={network_offwind_limit},\
geography={geography}"

def _config_from_variables(CONFIG_NAME, VARIABLES):

    CONSTANTS = _read_constants(CONFIG_NAME)
    SCENARIO = _get_scenario_key(CONSTANTS, VARIABLES)

    fname = f"../../data/result/{SCENARIO}/config.json"
    if not os.path.isfile(fname):
        print(f"Could not find file: {fname}")
        return None

    with open(fname, "r") as f:
        CONFIG = json.load(f)

    return CONFIG

def read_dashboard_available_variables(CONFIG_NAME):
    CONFIG_DEFINITION = _read_config_definition(CONFIG_NAME)
    
    return CONFIG_DEFINITION["scenarios"]

def all_data_from_variables(ROOT, CONFIG):
 
    # Setting variables based on config
    DATA_PATH=CONFIG["scenario"]["data-path"]

    CUTOUT = atlite.Cutout(f"{ROOT}../{DATA_PATH}/cutout.nc")
    SELECTION = gpd.read_file(f"{ROOT}../{DATA_PATH}/selection.shp")
    EEZ = gpd.read_file(f"{ROOT}../{DATA_PATH}/eez.shp")

    AVAIL_SOLAR = xr.open_dataarray(f"{ROOT}../{DATA_PATH}/avail_solar.nc")
    AVAIL_ONWIND = xr.open_dataarray(f"{ROOT}../{DATA_PATH}/avail_onwind.nc")
    AVAIL_OFFWIND = xr.open_dataarray(f"{ROOT}../{DATA_PATH}/avail_offwind.nc")

    AVAIL_CAPACITY_SOLAR = xr.open_dataarray(f"{ROOT}../{DATA_PATH}/avail_capacity_solar.nc")
    AVAIL_CAPACITY_ONWIND = xr.open_dataarray(f"{ROOT}../{DATA_PATH}/avail_capacity_onwind.nc")
    AVAIL_CAPACITY_OFFWIND = xr.open_dataarray(f"{ROOT}../{DATA_PATH}/avail_capacity_offwind.nc")

    ASSUMPTIONS = pd.read_pickle(f"{ROOT}../{DATA_PATH}/costs.pkl")

    DEMAND = pd.read_csv(f"{ROOT}../{DATA_PATH}/demand.csv", index_col=0, parse_dates=[0])

    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"{ROOT}../{DATA_PATH}/network.nc")

    STATISTICS = pd.read_pickle(f"{ROOT}../{DATA_PATH}/statistics.pkl")

    return [
        ASSUMPTIONS,
        DEMAND,
        NETWORK,
        STATISTICS,
        CUTOUT,
        SELECTION,
        EEZ,
        AVAIL_SOLAR,
        AVAIL_ONWIND,
        AVAIL_OFFWIND,
        AVAIL_CAPACITY_SOLAR,
        AVAIL_CAPACITY_ONWIND,
        AVAIL_CAPACITY_OFFWIND,
    ]

@st.cache_data
def demand_data_from_variables(ROOT, CONFIG):
    # Setting variables based on config
    DATA_PATH=CONFIG["scenario"]["data-path"]

    return pd.read_csv(f"{ROOT}../{DATA_PATH}/demand.csv", index_col=0, parse_dates=[0])

@st.cache_data
def statistics_data_from_variables(ROOT, CONFIG):
    # Setting variables based on config
    DATA_PATH=CONFIG["scenario"]["data-path"]

    STATISTICS = pd.read_pickle(f"{ROOT}../{DATA_PATH}/statistics.pkl")

    return STATISTICS

@st.cache_data
def network_data_from_variables(ROOT, CONFIG):
    # Setting variables based on config
    DATA_PATH=CONFIG["scenario"]["data-path"]

    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"{ROOT}../{DATA_PATH}/network.nc")

    return NETWORK

def ensure_default_variables(var_dict):
    if "load_target" not in var_dict:
        var_dict.load_target = 10
    if "network_nuclear" not in var_dict:
        var_dict.network_nuclear = False
    if "network_h2" not in var_dict:
        var_dict.network_h2 = True
    if "network_offwind" not in var_dict:
        var_dict.network_offwind = True
    if "network_biogas" not in var_dict:
        var_dict.network_biogas = "Ingen"
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
