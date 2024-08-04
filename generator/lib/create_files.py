import sys
import pandas as pd
import geopandas as gpd
import atlite
import xarray as xr
import pickle
import pypsa
import shutil
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths
from library.assumptions import read_assumptions
from library.weather import generate_cutout
from library.geography import availability_matrix, capacity_factor
from library.network import build_network
from generator.lib.collect_analytics import collect_data

# Process assumptions csv to dataframe and save pickle
def create_and_store_parameters(config):
    data_path = paths.output_path / config['scenario']['data-path']

    if (data_path / 'assumptions.pkl').is_file():
        print("assumptions.pkl already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    base_year = config["scenario"]["base-year"]
    target_year = config["scenario"]["target-year"]

    assumptions = read_assumptions(paths.input_path / 'assumptions.csv', base_year, target_year, config["base-currency"], config["exchange-rates"], config["scenario"]["discount-rate"])
    assumptions.to_pickle(data_path / 'assumptions.pkl')

# Create a cutout and store resulting files
def create_and_store_cutout(config):

    weather_start = '2023-01' # Temporary fix
    weather_end = '2023-12' # Temporary fix

    data_path = paths.output_path / 'geo' / f"{config['scenario']['geography_lan_code']}-{weather_start}-{weather_end}"

    if (data_path / 'cutout.nc').is_file():
        print("cutout.nc already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    cutout, selection, eez, index = generate_cutout(config['scenario']['geography_lan_code'], config['scenario']['geography_kom_code'], weather_start, weather_end)

    cutout.to_file(data_path / 'cutout.nc')
    selection.to_file(data_path / 'selection.shp')
    eez.to_file(data_path / 'eez.shp')
    index.to_series().to_csv(data_path / 'time_index.csv')

# Store availability matrix and capacity factor
def create_and_store_availability(config):
    weather_start = '2023-01' # Temporary fix
    weather_end = '2023-12' # Temporary fix

    data_path = paths.output_path / 'geo' / f"{config['scenario']['geography_lan_code']}-{weather_start}-{weather_end}"

    if (data_path / 'avail_solar.nc').is_file():
        print("Capacity series already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    CUTOUT = atlite.Cutout(data_path / 'cutout.nc')
    SELECTION = gpd.read_file(data_path / 'selection.shp')

    for key, value in config['models'].items():
        availability_matrix(CUTOUT, SELECTION, key).to_netcdf(data_path / f"avail_{key}.nc")
        capacity_factor(CUTOUT, SELECTION, key, value).to_netcdf(data_path / f"capacity_factor_{key}.nc")

# Store demand/load time series
def create_and_store_demand(config):

    data_path = paths.output_path / 'demand' / str(config['scenario']['load-target'])

    if (data_path / 'demand.csv').is_file():
        print("Demand series already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    # Load normalized load (for SE3 from file)
    load = pd.read_csv(paths.input_path / 'demand/normalized-load-2023-3h.csv', delimiter=',')

    # Create a new load using total yearly target from config and save as file
    load['se3'] = load['se3'] * config['scenario']['load-target'] * 1_000_000
    load.to_csv(data_path / 'demand.csv')

# Build network and store in file
def create_and_store_network(config):
    weather_start = '2023-01' # Temporary fix
    weather_end = '2023-12' # Temporary fix

    data_path = paths.output_path / config['scenario']['data-path']
    geo_data_path = paths.output_path / 'geo' / f"{config['scenario']['geography_lan_code']}-{weather_start}-{weather_end}"
    demand_data_path = paths.output_path / 'demand' / str(config['scenario']['load-target'])

    if (data_path / 'network.nc').is_file():
        print("Network already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    INDEX = pd.to_datetime(pd.read_csv(geo_data_path / 'time_index.csv')["0"])
    GEOGRAPHY = gpd.read_file(geo_data_path / 'selection.shp').total_bounds
    LOAD = pd.read_csv(demand_data_path / 'demand.csv')["se3"].values.flatten()
    ASSUMPTIONS = pd.read_pickle(data_path / 'assumptions.pkl')

    CAPACITY_FACTOR_SOLAR = xr.open_dataarray(geo_data_path / 'capacity_factor_solar.nc').values.flatten()
    CAPACITY_FACTOR_ONWIND = xr.open_dataarray(geo_data_path / 'capacity_factor_solar.nc').values.flatten()
    CAPACITY_FACTOR_OFFWIND = xr.open_dataarray(geo_data_path / 'capacity_factor_solar.nc').values.flatten()

    RESOLUTION = 3 #3h window for weather data and pypsa model optimization

    use_nuclear = bool(config['scenario']["network-nuclear"])
    use_offwind = bool(config['scenario']["network-offwind"])
    use_h2 = bool(config['scenario']["network-h2"])
    biogas_profile = str(config['scenario']["network-biogas"]) # Ingen, Liten, Mellan, Stor

    biogas_production_max_nominal = config["profiles"]["biogas"][biogas_profile]

    print(f"Using config:\n\th2:{use_h2}\n\tnuclear:{use_nuclear}\n\toffwind:{use_offwind}\n\tbiogas:{biogas_profile}")

    network = build_network(INDEX, RESOLUTION, GEOGRAPHY, LOAD, ASSUMPTIONS, CAPACITY_FACTOR_SOLAR, CAPACITY_FACTOR_ONWIND, CAPACITY_FACTOR_OFFWIND, use_offwind, use_h2, use_nuclear, biogas_production_max_nominal)

    network.export_to_netcdf(data_path / 'network.nc')

# Run optimization and store results
def create_and_store_optimize(config):

    data_path = paths.output_path / config['scenario']['data-path']

    if (data_path / 'statistics.pkl').is_file():
        print("Statistics file already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    
    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(data_path / 'network.nc')
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
    statistics.to_pickle(data_path / 'statistics.pkl')

    NETWORK.export_to_netcdf(data_path / 'network.nc')


def create_and_store_data_analytics(config):
    data_path = paths.output_path / config['scenario']['data-path']
    network_data_path = paths.output_path / 'network' / config['scenario']['data-path']

    if (data_path / 'network.pkl').is_file():
        print("Analytics file already exists, continue")
        return

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    
    if not network_data_path.exists():
        network_data_path.mkdir(parents=True, exist_ok=True)

    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(data_path / 'network.nc')
    
    with open(data_path / 'statistics.pkl', "rb") as fp:
        STATISTICS = pickle.load(fp)

    ASSUMPTIONS = pd.read_pickle(data_path / 'assumptions.pkl')

    # Organize a data collection optimized for data analytics
    data_collection = collect_data(NETWORK, STATISTICS, ASSUMPTIONS)
    
    #with (data_path / 'network.pkl').open('wb') as fp:
    #    pickle.dump(data_collection, fp)
    
    for key, value in data_collection.items():
        x = network_data_path / f"network_{key}.csv"
        if key == "table":
            value["data"].to_csv(network_data_path / f"network_{key}.csv")
            value["totals"].to_csv(network_data_path / f"network_{key}_totals.csv")
        elif key == "energy_compare":
            value["data"].to_csv(network_data_path / f"network_{key}.csv")
            value["series"].to_csv(network_data_path / f"network_{key}_series.csv")
        else:
            value.to_csv(network_data_path / f"network_{key}.csv")

def copy_input_data(config_name):
    if not (paths.output_path / 'assumptions.csv').is_file():
        shutil.copyfile(paths.input_path / 'assumptions.csv', paths.output_path / 'assumptions.csv')

    if not (paths.output_path / 'config.json').is_file():
        shutil.copyfile(paths.generator_path / 'configs' / f"{config_name}.json", paths.output_path / 'config.json')