import sys
import os.path

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from library.weather import generate_cutout

def create_and_store_cutout(config):
    scenario_config=config["scenario"]
    LAN_CODE = scenario_config["geography_lan_code"]
    KOM_CODE = scenario_config["geography_kom_code"]
    START=scenario_config["weather_start"]
    END=scenario_config["weather_end"]

    DATA_ROOT_PATH="data/result"
    GEO_KEY = f"{LAN_CODE}-{START}-{END}"
    DATA_PATH = f"{DATA_ROOT_PATH}/geo/{GEO_KEY}"

    if os.path.isfile(f"../{DATA_PATH}/cutout.nc"):
        print("Cutout: Files already exists, continue")
        return
    if not os.path.exists(f"../{DATA_PATH}"):
        os.makedirs(f"../{DATA_PATH}")

    cutout, selection, eez, index = generate_cutout(LAN_CODE, KOM_CODE, START, END)

    cutout.to_file(f"../{DATA_PATH}/cutout.nc")
    selection.to_file(f"../{DATA_PATH}/selection.shp")
    eez.to_file(f"../{DATA_PATH}/eez.shp")
    index.to_series().to_csv(f"../{DATA_PATH}/time_index.csv")
