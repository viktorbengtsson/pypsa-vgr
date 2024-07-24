import sys
import os.path
import geopandas as gpd
import atlite

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from library.geography import availability_matrix, capacity_factor

def create_and_store_availability(config):
    scenario_config=config["scenario"]
    LAN_CODE = scenario_config["geography_lan_code"]
    KOM_CODE = scenario_config["geography_kom_code"]
    START=scenario_config["weather_start"]
    END=scenario_config["weather_end"]

    DATA_ROOT_PATH="data/result"
    GEO_KEY = f"{LAN_CODE}-{START}-{END}"
    DATA_PATH = f"{DATA_ROOT_PATH}/geo/{GEO_KEY}"

    if os.path.isfile(f"../{DATA_PATH}/avail_solar.nc") & os.path.isfile(f"../{DATA_PATH}/capacity_factor_solar.nc"):
        print("Availability: Files already exists, continue")
        return
    if not os.path.exists(f"../{DATA_PATH}"):
        os.makedirs(f"../{DATA_PATH}")

    CUTOUT = atlite.Cutout(f"../{DATA_PATH}/cutout.nc")
    SELECTION = gpd.read_file(f"../{DATA_PATH}/selection.shp")

    availability_matrix(CUTOUT, SELECTION, 'solar').to_netcdf(f"../{DATA_PATH}/avail_solar.nc")
    capacity_factor(CUTOUT, SELECTION, 'solar', '').to_netcdf(f"../{DATA_PATH}/capacity_factor_solar.nc")
    availability_matrix(CUTOUT, SELECTION, 'onwind').to_netcdf(f"../{DATA_PATH}/avail_onwind.nc")
    capacity_factor(CUTOUT, SELECTION, 'onwind', config['onwind_turbine']).to_netcdf(f"../{DATA_PATH}/capacity_factor_onwind.nc")
    availability_matrix(CUTOUT, SELECTION, 'offwind').to_netcdf(f"../{DATA_PATH}/avail_offwind.nc")
    capacity_factor(CUTOUT, SELECTION, 'offwind', config['offwind_turbine']).to_netcdf(f"../{DATA_PATH}/capacity_factor_offwind.nc")

