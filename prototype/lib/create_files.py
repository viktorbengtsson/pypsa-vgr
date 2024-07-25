import sys
import os.path
import pandas as pd
import geopandas as gpd
import atlite
import xarray as xr
import pickle
import pypsa

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from library.assumptions import read_assumptions
from library.weather import generate_cutout
from library.geography import availability_matrix, capacity_factor
from library.network import build_network
from prototype.lib.collect_analytics import collect_data

def check_for_files(data_path, fname):
    if os.path.isfile(f"../{data_path}/{fname}"):
        print("Costs: Files already exists, continue")
        return
    if not os.path.exists(f"../{data_path}"):
        os.makedirs(f"../{data_path}")

# Process assumptions csv to dataframe and save pickle
def create_and_store_parameters(config):
    DATA_PATH = f"data/{config['scenario']['data-path']}"
    check_for_files(DATA_PATH, 'costs.pkl')

    base_year = config["scenario"]["base-year"]
    target_year = config["scenario"]["target-year"]

    assumptions = read_assumptions(f"../data/assumptions.csv", base_year, target_year, config["base-currency"], config["exchange-rates"], config["scenario"]["discount-rate"])
    assumptions.to_pickle(f"../{DATA_PATH}/costs.pkl")

# Create a cutout and store resulting files
def create_and_store_cutout(config):
    DATA_PATH = f"data/result/geo/{config['scenario']['geography_lan_code']}-{config['scenario']['weather_start']}-{config['scenario']['weather_end']}"
    check_for_files(DATA_PATH, 'cutout.nc')

    cutout, selection, eez, index = generate_cutout(config['scenario']['geography_lan_code'], config['scenario']['geography_kom_code'], config['scenario']['weather_start'], config['scenario']['weather_end'])

    cutout.to_file(f"../{DATA_PATH}/cutout.nc")
    selection.to_file(f"../{DATA_PATH}/selection.shp")
    eez.to_file(f"../{DATA_PATH}/eez.shp")
    index.to_series().to_csv(f"../{DATA_PATH}/time_index.csv")

# Store availability matrix and capacity factor
def create_and_store_availability(config):
    DATA_PATH = f"data/result/geo/{config['scenario']['geography_lan_code']}-{config['scenario']['weather_start']}-{config['scenario']['weather_end']}"
    check_for_files(DATA_PATH, 'avail_solar.nc')

    CUTOUT = atlite.Cutout(f"../{DATA_PATH}/cutout.nc")
    SELECTION = gpd.read_file(f"../{DATA_PATH}/selection.shp")

    for key, value in config['models'].items():
        availability_matrix(CUTOUT, SELECTION, key).to_netcdf(f"../{DATA_PATH}/avail_{key}.nc")
        capacity_factor(CUTOUT, SELECTION, key, value).to_netcdf(f"../{DATA_PATH}/capacity_factor_{key}.nc")

# Store demand/load time series
def create_and_store_demand(config):
    DATA_PATH = f"data/result/{config['scenario']['demand']}/{config['scenario']['load-target']}"
    check_for_files(DATA_PATH, 'demand.csv')

    # Load normalized load (for SE3 from file)
    load = pd.read_csv(f"../data/demand/normalized-load-2023-3h.csv", delimiter=',')

    # Create a new load using total yearly target from config and save as file
    load['se3'] = load['se3'] * config['scenario']['load-target'] * 1_000_000
    load.to_csv(f"../{DATA_PATH}/demand.csv")

# Build network and store in file
def create_and_store_network(config):
    DATA_PATH = f"data/{config['scenario']['data-path']}"
    GEO_DATA_PATH = f"data/result/geo/{config['scenario']['geography_lan_code']}-{config['scenario']['weather_start']}-{config['scenario']['weather_end']}"
    DEMAND_DATA_PATH = f"data/result/{config['scenario']['demand']}/{config['scenario']['load-target']}"
    check_for_files(DATA_PATH, 'network.nc')
    
    INDEX = pd.to_datetime(pd.read_csv(f"../{GEO_DATA_PATH}/time_index.csv")["0"])
    GEOGRAPHY = gpd.read_file(f"../{GEO_DATA_PATH}/selection.shp").total_bounds
    LOAD = pd.read_csv(f"../{DEMAND_DATA_PATH}/demand.csv")["se3"].values.flatten()
    ASSUMPTIONS = pd.read_pickle(f"../{DATA_PATH}/costs.pkl")

    CAPACITY_FACTOR_SOLAR = xr.open_dataarray(f"../{GEO_DATA_PATH}/capacity_factor_solar.nc").values.flatten()
    CAPACITY_FACTOR_ONWIND = xr.open_dataarray(f"../{GEO_DATA_PATH}/capacity_factor_solar.nc").values.flatten()
    CAPACITY_FACTOR_OFFWIND = xr.open_dataarray(f"../{GEO_DATA_PATH}/capacity_factor_solar.nc").values.flatten()

    RESOLUTION = 3 #3h window for weather data and pypsa model optimization

    use_nuclear = bool(config['scenario']["network-nuclear"])
    use_offwind = bool(config['scenario']["network-offwind"])
    use_h2 = bool(config['scenario']["network-h2"])
    biogas_profile = str(config['scenario']["network-biogas"]) # Ingen, Liten, Mellan, Stor

    biogas_production_max_nominal = config["profiles"]["biogas"][biogas_profile]

    print(f"Using config:\n\th2:{use_h2}\n\tnuclear:{use_nuclear}\n\toffwind:{use_offwind}\n\tbiogas:{biogas_profile}")

    network = build_network(INDEX, RESOLUTION, GEOGRAPHY, LOAD, ASSUMPTIONS, CAPACITY_FACTOR_SOLAR, CAPACITY_FACTOR_ONWIND, CAPACITY_FACTOR_OFFWIND, use_offwind, use_h2, use_nuclear, biogas_production_max_nominal)

    network.export_to_netcdf(f"../{DATA_PATH}/network.nc")

# Run optimization and store results
def create_and_store_optimize(config):
    DATA_PATH = f"data/{config['scenario']['data-path']}"
    check_for_files(DATA_PATH, 'statistics.pkl')
    
    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"../{DATA_PATH}/network.nc")
    MODEL = NETWORK.optimize.create_model()

    use_offwind = bool(config["scenario"]["network-offwind"])
    
    generator_capacity = MODEL.variables["Generator-p_nom"]
    link_capacity = MODEL.variables["Link-p_nom"]
    
    ## Offwind constraint
    if use_offwind:
        offwind_percentage = 0.5

        offwind_constraint = (1 - offwind_percentage) / offwind_percentage * generator_capacity.loc['Offwind park'] - generator_capacity.loc['Onwind park']
        MODEL.add_constraints(offwind_constraint == 0, name="Offwind_constraint")

    ## Battery charge/discharge ratio
    lhs = link_capacity.loc["Battery charge"] - NETWORK.links.at["Battery charge", "efficiency"] * link_capacity.loc["Battery discharge"]
    MODEL.add_constraints(lhs == 0, name="Link-battery_fix_ratio")
    
    # Run optimization
    NETWORK.optimize.solve_model(solver_name='highs')

    # Save results
    statistics = NETWORK.statistics()
    statistics.to_pickle(f"../{DATA_PATH}/statistics.pkl")

    NETWORK.export_to_netcdf(f"../{DATA_PATH}/network.nc")


def create_and_store_data_analytics(config):
    DATA_PATH = f"data/{config['scenario']['data-path']}"
    check_for_files(DATA_PATH, 'network.pkl')

    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"../{DATA_PATH}/network.nc")
    
    with open(f"../{DATA_PATH}/statistics.pkl", "rb") as f:
        STATISTICS = pickle.load(f)

    ASSUMPTIONS = pd.read_pickle(f"../{DATA_PATH}/costs.pkl")

    # Organize a data collection optimized for data analytics
    data_collection = collect_data(NETWORK, STATISTICS, ASSUMPTIONS)
    
    fname = f"../{DATA_PATH}/network.pkl"
    with open(fname, "wb") as f:
        pickle.dump(data_collection, f)
