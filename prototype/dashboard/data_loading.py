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

    demand_target = VARIABLES.get("demand_target") or 0.03
    load_target = VARIABLES.get("load_target") or 10
    network_nuclear = VARIABLES.get("network_nuclear") or "off"
    network_h2 = VARIABLES.get("network_h2") or "off"
    network_biogas = VARIABLES.get("network_biogas") or "small"
    network_onwind_limit = VARIABLES.get("network_onwind_limit")
    network_offwind_limit = VARIABLES.get("network_offwind_limit")
    geography = VARIABLES.get("geography") or "14"

    return f"weather={weather_data_year},\
costs={costs_data_year},\
demand={demand_data_year},\
demand-target={demand_target},\
load-target={load_target},\
network-nuclear={network_nuclear},\
network-h2={network_h2},\
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

def deep_data_from_variables(ROOT, CONFIG):
 
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

    data = essential_data_from_variables(ROOT, CONFIG)
    data.extend([
        CUTOUT,
        SELECTION,
        EEZ,
        AVAIL_SOLAR,
        AVAIL_ONWIND,
        AVAIL_OFFWIND,
        AVAIL_CAPACITY_SOLAR,
        AVAIL_CAPACITY_ONWIND,
        AVAIL_CAPACITY_OFFWIND,
    ])
    
    return data


def essential_data_from_variables(ROOT, CONFIG):

    # Setting variables based on config
    DATA_PATH=CONFIG["scenario"]["data-path"]

    ASSUMPTIONS = pd.read_pickle(f"{ROOT}../{DATA_PATH}/costs.pkl")

    DEMAND = pd.read_csv(f"{ROOT}../{DATA_PATH}/demand.csv")

    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"{ROOT}../{DATA_PATH}/network.nc")

    STATISTICS = pd.read_pickle(f"{ROOT}../{DATA_PATH}/statistics.pkl")

    return [
        ASSUMPTIONS,
        DEMAND,
        NETWORK,
        STATISTICS
    ]

def ensure_default_variables(var_dict):
    if "demand_target" not in var_dict:
        var_dict.demand_target = 0.03
    if "load_target" not in var_dict:
        var_dict.load_target = 10
    if "network_nuclear" not in var_dict:
        var_dict.network_nuclear = False
    if "network_h2" not in var_dict:
        var_dict.network_h2 = False
    if "network_biogas" not in var_dict:
        var_dict.network_biogas = "Liten"
    if "network_onwind_limit" not in var_dict:
        var_dict.network_onwind_limit = None
    if "network_offwind_limit" not in var_dict:
        var_dict.network_offwind_limit = None
    if "geography" not in var_dict:
        var_dict.geography = "14"

    return {
        "geography": var_dict.get("geography"),
        "demand_target": float(var_dict.get("demand_target")),
        "load_target": int(var_dict.get("load_target")),
        "network_nuclear": var_dict.get("network_nuclear"),
        "network_h2": var_dict.get("network_h2"),
        "network_biogas": var_dict.get("network_biogas"),
        "network_onwind_limit": var_dict.get("network_onwind_limit"),
        "network_offwind_limit": var_dict.get("network_offwind_limit"),
    }