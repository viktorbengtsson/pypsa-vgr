import sys
import os.path
import pandas as pd
import geopandas as gpd
import xarray as xr

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from library.model import build_network

def create_and_store_network(config):
    scenario_config=config["scenario"]
    LAN_CODE = scenario_config["geography_lan_code"]
    START=scenario_config["weather_start"]
    END=scenario_config["weather_end"]
    YEAR=scenario_config["demand"]
    TARGET=scenario_config["load-target"]

    DATA_ROOT_PATH="data/result"
    GEO_KEY = f"{LAN_CODE}-{START}-{END}"
    DEMAND_KEY = f"{YEAR}/{TARGET}"

    DATA_PATH =scenario_config["data-path"]    
    DATA_PATH = f"data/{DATA_PATH}"
    GEO_DATA_PATH = f"{DATA_ROOT_PATH}/geo/{GEO_KEY}"
    DEMAND_DATA_PATH = f"{DATA_ROOT_PATH}/{DEMAND_KEY}"

    if os.path.isfile(f"../{DATA_PATH}/network.nc"):
        print("Network: Files already exists, continue")
        return
    if not os.path.exists(f"../{DATA_PATH}"):
        os.makedirs(f"../{DATA_PATH}")
    
    INDEX = pd.to_datetime(pd.read_csv(f"../{GEO_DATA_PATH}/time_index.csv")["0"])
    GEOGRAPHY = gpd.read_file(f"../{GEO_DATA_PATH}/selection.shp").total_bounds
    LOAD = pd.read_csv(f"../{DEMAND_DATA_PATH}/demand.csv")["se3"].values.flatten()
    ASSUMPTIONS = pd.read_pickle(f"../{DATA_PATH}/costs.pkl")

    CAPACITY_FACTOR_SOLAR = xr.open_dataarray(f"../{GEO_DATA_PATH}/capacity_factor_solar.nc").values.flatten()
    CAPACITY_FACTOR_ONWIND = xr.open_dataarray(f"../{GEO_DATA_PATH}/capacity_factor_solar.nc").values.flatten()
    CAPACITY_FACTOR_OFFWIND = xr.open_dataarray(f"../{GEO_DATA_PATH}/capacity_factor_solar.nc").values.flatten()


    RESOLUTION = 3 #3h window for weather data and pypsa model optimization
    parameters = pd.read_csv("../data/assumptions.csv")
    parameters.set_index(['technology', 'parameter'], inplace=True)

    use_nuclear = bool(scenario_config["network-nuclear"])
    use_offwind = bool(scenario_config["network-offwind"])
    use_h2 = bool(scenario_config["network-h2"])
    biogas_profile = str(scenario_config["network-biogas"]) # Ingen, Liten, Mellan, Stor

    biogas_production_max_nominal = config["profiles"]["biogas"][biogas_profile]

    print(f"Using config:\n\th2:{use_h2}\n\tnuclear:{use_nuclear}\n\toffwind:{use_offwind}\n\tbiogas:{biogas_profile}")

    network = build_network(INDEX, RESOLUTION, GEOGRAPHY, LOAD, ASSUMPTIONS, CAPACITY_FACTOR_SOLAR, CAPACITY_FACTOR_ONWIND, CAPACITY_FACTOR_OFFWIND, use_offwind, use_h2, use_nuclear, biogas_production_max_nominal)

    network.export_to_netcdf(f"../{DATA_PATH}/network.nc")
