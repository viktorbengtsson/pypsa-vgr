import sys
import pandas as pd
import geopandas as gpd
import json
import xarray as xr
import pickle
import pypsa
import shutil
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths
from library.assumptions import read_assumptions
from library.network import build_network
from generator.lib.tools import delete_file

# Process assumptions csv to dataframe and save csv
def create_and_store_parameters(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (data_path / 'assumptions.csv').is_file():
        print("assumptions.csv already exists, continue")
        return

    assumptions = read_assumptions(paths.input_path / 'assumptions.csv', 
                                   config["base-year"], config["scenario"]["target-year"], config["base-currency"], config["exchange-rates"], config["discount-rate"]
                                   )
    assumptions.to_csv(data_path / 'assumptions.csv')


# Check that weather files exist (if not see /input/weather/generate-weather.ipynb)
def check_weather_files(config):
    weather_path = paths.input_path / 'weather'

    cutout_files = list(weather_path.glob(f"cutout-{config['scenario']['geography']}-*.nc"))
    selection_files = list(weather_path.glob(f"selection-{config['scenario']['geography']}-*.shp"))
    index_files = list(weather_path.glob(f"index-{config['scenario']['geography']}-*.csv"))

    if not (len(cutout_files) > 0 and len(selection_files) > 0 and len(index_files) > 0):
        print(f"Weather files do not exist for geography {config['scenario']['geography']}. Please see /input/weather/generate-weather.ipynb")


# Check that renewables files exist (if not see /input/renewables/generate-renewables.ipynb)
def check_renewables_files(config):
    renewables_path = paths.input_path / 'renewables'

    avail_matrix_files = list(renewables_path.glob(f"availability-matrix-{config['scenario']['geography']}-*.nc"))    
    cap_fac_files = list(renewables_path.glob(f"capacity-factor-{config['scenario']['geography']}-*.nc"))    

    if not (len(avail_matrix_files) > 0 and len(cap_fac_files) > 0):
        print(f"Renewables files do not exist for geography {config['scenario']['geography']}. Please see /input/renewables/generate-renewables.ipynb")


# Store demand/load time series
def create_and_store_demand(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (data_path / 'demand.csv').is_file():
        print("Demand series already exists, continue")
        return

    # Load normalized load (for SE3 from file)
    demand = pd.read_csv(paths.input_path / 'demand/normalized-demand-2023-3h.csv', delimiter=',', index_col=0, parse_dates=True)

    # Create a new load using total yearly target from config and save as file
    demand['value'] = config['scenario']['load-target'] * demand['value'] * 1_000_000
    demand.to_csv(data_path / 'demand.csv')


# Build network and store in file
def create_and_store_network(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (data_path / 'network.nc').is_file():
        print("Network already exists, continue")
        return

    # Load weather data config
    with (paths.input_path / 'config.json').open('r') as f:
        weather_config = json.load(f)

    weather_path = paths.input_path / 'weather'
    renewables_path = paths.input_path / 'renewables'

    index = pd.to_datetime(pd.read_csv(weather_path / f"index-{config['scenario']['geography']}-{weather_config['weather-start']}-{weather_config['weather-end']}.csv")['0'])
    resolution = 3
    geography = gpd.read_file(weather_path / f"selection-{config['scenario']['geography']}-{weather_config['weather-start']}-{weather_config['weather-end']}.shp").total_bounds
    demand = pd.read_csv(data_path / 'demand.csv', index_col=0).values.flatten()
    assumptions = pd.read_csv(data_path / 'assumptions.csv', index_col=[0,1])

    capacity_factor_solar = xr.open_dataarray(renewables_path / f"capacity-factor-{config['scenario']['geography']}-{weather_config['weather-start']}-{weather_config['weather-end']}-solar.nc").values.flatten()
    capacity_factor_onwind = xr.open_dataarray(renewables_path / f"capacity-factor-{config['scenario']['geography']}-{weather_config['weather-start']}-{weather_config['weather-end']}-onwind.nc").values.flatten()
    capacity_factor_offwind = xr.open_dataarray(renewables_path / f"capacity-factor-{config['scenario']['geography']}-{weather_config['weather-start']}-{weather_config['weather-end']}-offwind.nc").values.flatten()

    use_nuclear = bool(config['scenario']["network-nuclear"])
    use_offwind = bool(config['scenario']["network-offwind"])
    use_h2 = bool(config['scenario']["network-h2"])
    biogas_profile = str(config['scenario']["network-biogas"]) # Ingen, Liten, Mellan, Stor

    biogas_production_max_nominal = config["profiles"]["biogas"][biogas_profile]

    print(f"Using config:\n\th2:{use_h2}\n\tnuclear:{use_nuclear}\n\toffwind:{use_offwind}\n\tbiogas:{biogas_profile}")

    network = build_network(index, resolution, geography, demand, assumptions, capacity_factor_solar, capacity_factor_onwind, capacity_factor_offwind, use_offwind, use_h2, use_nuclear, biogas_production_max_nominal)

    network.export_to_netcdf(data_path / 'network.nc')

# Run optimization and store results
def create_and_store_optimize(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')
    model = network.optimize.create_model()

    use_offwind = bool(config["scenario"]["network-offwind"])
    
    generator_capacity = model.variables["Generator-p_nom"]
    link_capacity = model.variables["Link-p_nom"]
    
    ## Offwind constraint
    if use_offwind:
        offwind_percentage = 0.5

        offwind_constraint = (1 - offwind_percentage) / offwind_percentage * generator_capacity.loc['offwind'] - generator_capacity.loc['onwind']
        model.add_constraints(offwind_constraint == 0, name="Offwind_constraint")

    ## Battery charge/discharge ratio
    lhs = link_capacity.loc["Battery charge"] - network.links.at["Battery charge", "efficiency"] * link_capacity.loc["Battery discharge"]
    model.add_constraints(lhs == 0, name="Link-battery_fix_ratio")

    # Run optimization
    network.optimize.solve_model(solver_name='highs')

    # Save results
    network.export_to_netcdf(data_path / 'network.nc')

def create_and_store_results(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (paths.output_path / 'config.json').is_file():
        print("Results files already exist, continue")
        return
    
    ## Copy config to output
    shutil.copy(paths.generator_path / 'configs' / f"{config['config-name']}.json", paths.output_path / 'scenarios.json')
    
    ## Create files for demand data
    demand_t_3h = pd.read_csv(data_path / 'demand.csv', index_col=0, parse_dates=True) * 3
    demand_t_1d = demand_t_3h.resample('1d').sum()
    demand_t_1w = demand_t_3h.resample('1w').sum()

    demand_path = data_path / 'demand'
    demand_path.mkdir(parents=True, exist_ok=True)
    demand_t_3h.to_csv(demand_path / 'demand_t_3h.csv')
    demand_t_1d.to_csv(demand_path / 'demand_t_1d.csv')
    demand_t_1w.to_csv(demand_path / 'demand_t_1w.csv')

    
    # Load the results from the pypsa network
    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')

    ## Create generators data
    generators = network.generators[['p_nom_mod', 'p_nom_opt', 'capital_cost', 'marginal_cost']]
    generators['mod_units'] = generators['p_nom_opt']/generators['p_nom_mod']

    generators_power_t_3h = network.generators_t.p *3
    generators_power_t_1d = generators_power_t_3h.resample('1d').sum()
    generators_power_t_1w = generators_power_t_3h.resample('1w').sum()
    
    for generator in generators.index:
        generator_path = data_path / 'generators' / generator
        generator_path.mkdir(parents=True, exist_ok=True)
        generators.loc[generator].to_csv(generator_path / 'details.csv')
        generators_power_t_3h[generator].to_csv(generator_path / 'power_t_3h.csv')
        generators_power_t_1d[generator].to_csv(generator_path / 'power_t_1d.csv')
        generators_power_t_1w[generator].to_csv(generator_path / 'power_t_1w.csv')

    ## Create stores data
    stores = network.stores[['e_nom_mod', 'e_nom_opt', 'capital_cost', 'marginal_cost']]
    stores['mod_units'] = stores['e_nom_opt']/stores['e_nom_mod']

    stores_power_t_3h = network.stores_t.p * 3
    stores_power_t_1d = stores_power_t_3h.resample('1d').sum()
    stores_power_t_1w = stores_power_t_3h.resample('1w').sum()
    
    for store in stores.index:
        stores_path = data_path / 'stores' / store
        stores_path.mkdir(parents=True, exist_ok=True)
        stores.loc[store].to_csv(stores_path / 'details.csv')
        stores_power_t_3h[store].to_csv(stores_path / 'power_t_3h.csv')
        stores_power_t_1d[store].to_csv(stores_path / 'power_t_1d.csv')
        stores_power_t_1w[store].to_csv(stores_path / 'power_t_1w.csv')
        
def clear_working_files(config):
    data_path = paths.output_path / config['scenario']['data-path']
    delete_file(data_path / 'demand.csv')
    delete_file(data_path / 'network.nc')


'''
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
'''
