import sys
import pandas as pd
import numpy as np
import geopandas as gpd
import json
import xarray as xr
import pypsa
import shutil
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths
from library.assumptions import read_assumptions
from library.network import build_network
from generator.lib.tools import delete_file

def _get_geo(config):
    keys = config['scenario']['geography'].split(":", 1)
    geo = { "weather": keys[0], "section": keys[1] if len(keys) > 1 else keys[0] }
    geo["section_key"] = geo["weather"] if geo["weather"] == geo["section"] else f"{geo['weather']}-{geo['section']}"
    return geo

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
    geo = _get_geo(config)

    cutout_files = list(weather_path.glob(f"cutout-{geo['weather']}-*.nc"))
    selection_files = list(weather_path.glob(f"selection-{geo['section_key']}-*.shp"))
    index_files = list(weather_path.glob(f"index-{geo['weather']}-*.csv"))

    if not (len(cutout_files) > 0 and len(selection_files) > 0 and len(index_files) > 0):
        print(f"Weather files do not exist for geography weather={geo['weather']}, section={geo['section']}. Please see /input/weather/generate-weather.ipynb")


# Check that renewables files exist (if not see /input/renewables/generate-renewables.ipynb)
def check_renewables_files(config):
    renewables_path = paths.input_path / 'renewables'
    geo = _get_geo(config)

    avail_matrix_files = list(renewables_path.glob(f"availability-matrix-{geo['section_key']}-*.nc"))    
    cap_fac_files = list(renewables_path.glob(f"capacity-factor-{geo['section_key']}-*.nc"))    

    if not (len(avail_matrix_files) > 0 and len(cap_fac_files) > 0):
        print(f"Renewables files do not exist for geography {geo['section_key']}. Please see /input/renewables/generate-renewables.ipynb")


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
    geo = _get_geo(config)

    index = pd.to_datetime(pd.read_csv(weather_path / f"index-{geo['weather'][:2]}-{weather_config['weather-start']}-{weather_config['weather-end']}.csv")['0'])
    resolution = 3
    geography = gpd.read_file(weather_path / f"selection-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}.shp").total_bounds
    demand = pd.read_csv(data_path / 'demand.csv', index_col=0).values.flatten()
    assumptions = pd.read_csv(data_path / 'assumptions.csv', index_col=[0,1])

    capacity_factor_solar = xr.open_dataarray(renewables_path / f"capacity-factor-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}-solar.nc").values.flatten()
    capacity_factor_onwind = xr.open_dataarray(renewables_path / f"capacity-factor-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}-onwind.nc").values.flatten()
    capacity_factor_offwind = xr.open_dataarray(renewables_path / f"capacity-factor-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}-offwind.nc").values.flatten()

    #use_nuclear = bool(config['scenario']["network-nuclear"])
    offwind = bool(config['scenario']["offwind"])
    h2 = bool(config['scenario']["h2"])
    biogas_limit = config['scenario']["biogas-limit"]
    h2_initial = config['h2-initial']

    print(f"Using config:\n\th2:{h2}\n\toffwind:{offwind}\n\tbiogas:{biogas_limit}")

    network = build_network(index, resolution, geography, demand, assumptions, capacity_factor_solar, capacity_factor_onwind, capacity_factor_offwind, offwind, h2, h2_initial, biogas_limit)

    network.export_to_netcdf(data_path / 'network.nc')

# Run optimization and store results
def create_and_store_optimize(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')
    model = network.optimize.create_model()

    offwind = bool(config["scenario"]["offwind"])
    
    ## TODO: UPDATE THIS CONSTRAINT AFTER WE GET A NEW SOLVER
    ## Offwind constraint
    if False:
        generator_capacity = model.variables["Generator-p_nom"]
        offwind_percentage = config['offwind-ratio']

        offwind_constraint = (1 - offwind_percentage) / offwind_percentage * generator_capacity.loc['offwind'] - generator_capacity.loc['onwind']
        model.add_constraints(offwind_constraint == 0, name="Offwind_constraint")

    ## Battery charge/discharge ratio
    link_capacity = model.variables["Link-p_nom"]
    lhs = link_capacity.loc["battery-charge"] - network.links.at["battery-charge", "efficiency"] * link_capacity.loc["battery-discharge"]
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
    
    use_offwind = bool(config["scenario"]["offwind"])

    ## Copy config to output
    shutil.copy(paths.generator_path / 'configs' / f"{config['config-name']}.json", paths.output_path / 'scenarios.json')
    
    ## Create files for demand data
    demand_t_3h = pd.read_csv(data_path / 'demand.csv', index_col=0, parse_dates=True) * 3
    demand_t_1d = demand_t_3h.resample('1d').sum()
    demand_t_1w = demand_t_3h.resample('1W').sum()
    demand_t_1M = demand_t_3h.resample('1ME').sum()

    demand_path = data_path / 'demand'
    demand_path.mkdir(parents=True, exist_ok=True)
    demand_t_3h.to_csv(demand_path / 'demand_t_3h.csv')
    demand_t_1d.to_csv(demand_path / 'demand_t_1d.csv')
    demand_t_1w.to_csv(demand_path / 'demand_t_1w.csv')
    demand_t_1M.to_csv(demand_path / 'demand_t_1M.csv')

    
    # Load the results from the pypsa network
    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')

    ## Create generators data and curtailment data (renewable generators only)
    generators = network.generators[['p_nom_mod', 'p_nom_opt', 'capital_cost', 'marginal_cost']].copy()
    generators['mod_units'] = generators['p_nom_opt']/generators['p_nom_mod']
    generators['total_energy'] = network.generators_t.p.sum().round(9) * 3

    if use_offwind:
        renewable_generators = ['solar', 'onwind', 'offwind']
    else:
        renewable_generators = ['solar', 'onwind']

    generators_power_t_3h = network.generators_t.p.round(9) *3
    generators_power_t_1d = generators_power_t_3h.resample('1d').sum()
    generators_power_t_1w = generators_power_t_3h.resample('1W').sum()
    generators_power_t_1M = generators_power_t_3h.resample('1ME').sum()

    curtailment_power_t_3h = (network.generators_t.p_max_pu[renewable_generators].round(9) * network.generators.loc[renewable_generators]['p_nom_opt'] - network.generators_t.p[renewable_generators].round(9)) * 3
    curtailment_power_t_1d = curtailment_power_t_3h.resample('1d').sum()
    curtailment_power_t_1w = curtailment_power_t_3h.resample('1W').sum()
    curtailment_power_t_1M = curtailment_power_t_3h.resample('1ME').sum()

    annual_curtailment = 1 - network.generators_t.p[renewable_generators].sum()/(network.generators_t.p_max_pu[renewable_generators].sum() * network.generators.loc[renewable_generators]['p_nom_opt'])
    annual_curtailment.replace([np.inf, -np.inf], 0, inplace=True)
    generators['curtailment'] = annual_curtailment

    for generator in generators.index:
        generator_path = data_path / 'generators' / generator
        generator_path.mkdir(parents=True, exist_ok=True)
        generators.loc[generator].to_csv(generator_path / 'details.csv')
        generators_power_t_3h[generator].to_csv(generator_path / 'power_t_3h.csv')
        generators_power_t_1d[generator].to_csv(generator_path / 'power_t_1d.csv')
        generators_power_t_1w[generator].to_csv(generator_path / 'power_t_1w.csv')
        generators_power_t_1M[generator].to_csv(generator_path / 'power_t_1M.csv')

        if generator in renewable_generators:
            curtailment_power_t_3h[generator].to_csv(generator_path / 'curtailment_t_3h.csv')
            curtailment_power_t_1d[generator].to_csv(generator_path / 'curtailment_t_1d.csv')
            curtailment_power_t_1w[generator].to_csv(generator_path / 'curtailment_t_1w.csv')
            curtailment_power_t_1M[generator].to_csv(generator_path / 'curtailment_t_1M.csv')

    ## Add active links data (battery inverters, electrolysis, and gas turbines)
    links_charge = ['battery-charge']
    links_discharge = ['battery-discharge']
    if config['scenario']['h2']:
        links_charge += ['h2-electrolysis']
    if config['scenario']['h2'] or config['scenario']['biogas-limit'] > 0:
        links_discharge += ['gas-turbine']
    links = network.links.loc[links_charge + links_discharge][['p_nom_opt', 'p_nom_mod', 'capital_cost', 'marginal_cost']].copy()
    links['mod_units'] = links['p_nom_opt']/links['p_nom_mod']

    links_power_t_3h = -network.links_t.p0[links_charge].round(9)
    links_power_t_3h[links_discharge] = -network.links_t.p1[links_discharge]
    links_power_t_1d = links_power_t_3h.resample('1d').sum()
    links_power_t_1w = links_power_t_3h.resample('1W').sum()
    links_power_t_1M = links_power_t_3h.resample('1ME').sum()

    for link in links_charge+links_discharge:
        link_path = data_path / 'converters' / link
        link_path.mkdir(parents=True, exist_ok=True)
        links.loc[link].to_csv(link_path / 'details.csv')
        links_power_t_3h[link].to_csv(link_path / 'power_t_3h.csv')
        links_power_t_1d[link].to_csv(link_path / 'power_t_1d.csv')
        links_power_t_1w[link].to_csv(link_path / 'power_t_1w.csv')
        links_power_t_1M[link].to_csv(link_path / 'power_t_1M.csv')

    ## Create stores data
    stores = network.stores[['e_nom_mod', 'e_nom_opt', 'capital_cost', 'marginal_cost']].copy()
    stores['mod_units'] = stores['e_nom_opt']/stores['e_nom_mod']

    stores_power_t_3h = network.stores_t.p.round(9) * 3
    stores_power_t_1d = stores_power_t_3h.resample('1d').sum()
    stores_power_t_1w = stores_power_t_3h.resample('1W').sum()
    stores_power_t_1M = stores_power_t_3h.resample('1ME').sum()
    
    for store in stores.index:
        store_path = data_path / 'stores' / store
        store_path.mkdir(parents=True, exist_ok=True)
        stores.loc[store].to_csv(store_path / 'details.csv')
        stores_power_t_3h[store].to_csv(store_path / 'power_t_3h.csv')
        stores_power_t_1d[store].to_csv(store_path / 'power_t_1d.csv')
        stores_power_t_1w[store].to_csv(store_path / 'power_t_1w.csv')
        stores_power_t_1M[store].to_csv(store_path / 'power_t_1M.csv')

    ## Create sufficiency data
    backstop_3h = network.generators_t.p['backstop'] * 3
    backstop_1d = backstop_3h.resample('1d').sum()
    backstop_1w = backstop_3h.resample('1W').sum()
    backstop_1M = backstop_3h.resample('1ME').sum()

    load_3h = network.loads_t.p.squeeze() * 3
    load_1d = load_3h.resample('1d').sum().squeeze()
    load_1w = load_3h.resample('1W').sum().squeeze()
    load_1M = load_3h.resample('1ME').sum().squeeze()

    sufficiency_3h = (1 - backstop_3h/load_3h).round(4)
    sufficiency_1d = (1 - backstop_1d/load_1d).round(4)
    sufficiency_1w = (1 - backstop_1w/load_1w).round(4)
    sufficiency_1M = (1 - backstop_1M/load_1M).round(4)

    performance_path = data_path / 'performance'
    performance_path.mkdir(parents=True, exist_ok=True)
    sufficiency_3h.to_csv(performance_path / 'sufficiency_t_3h.csv')
    sufficiency_1d.to_csv(performance_path / 'sufficiency_t_1d.csv')
    sufficiency_1w.to_csv(performance_path / 'sufficiency_t_1w.csv')
    sufficiency_1M.to_csv(performance_path / 'sufficiency_t_1M.csv')

    ## Create performance metrics
    performance = pd.DataFrame(columns=['Value'])
    performance.loc['Total energy'] = round((network.loads_t.p.sum().iloc[0] - network.generators_t.p['backstop'].sum()) * 3,2)
    performance.loc['Backstop energy'] = network.generators_t.p['backstop'].sum().round(2) * 3
    performance.loc['Sufficiency'] = round((network.loads_t.p.sum().iloc[0] - network.generators_t.p['backstop'].sum()) / network.loads_t.p.sum().iloc[0],4)
    performance.loc['Shortfall'] = round(network.generators_t.p['backstop'].sum() / network.loads_t.p.sum().iloc[0],4)

    performance.to_csv(performance_path / 'performance_metrics.csv')

    worst = pd.DataFrame(columns=['Time', 'Sufficiency'])
    worst.loc['1d'] = [sufficiency_1d.nsmallest(1).index[0], sufficiency_1d.nsmallest(1).iloc[0].round(4)]
    worst.loc['1w'] = [sufficiency_1w.nsmallest(1).index[0], sufficiency_1w.nsmallest(1).iloc[0].round(4)]
    worst.loc['1M'] = [sufficiency_1M.nsmallest(1).index[0], sufficiency_1M.nsmallest(1).iloc[0].round(4)]

    worst.to_csv(performance_path / 'worst.csv')

    days_below = pd.DataFrame(columns=['Days'])
    for threshold in np.arange(0.95, 0, -0.05).round(2):
        days_below.loc[threshold] = (sufficiency_1d < threshold).sum()

    days_below.to_csv(performance_path / 'days_below.csv')


    ## Create overall network data

    ''' FOR SOME REASON I AM NOT GETTING MARGINAL_PRICES FROM THE MODEL. NEED TO INVESTIGATE THIS.
    ## Create the buses data
    buses = network.buses.index
    if len(network.buses_t.marginal_price.columns) > 0:
        marginal_price_t_3h = network.buses_t.marginal_price
    else:
        marginal_price_t_3h[buses] = len(network.buses_t.marginal_price.index) * [0]
    marginal_price_t_1d = network.buses_t.marginal_price.resample('1d')
    marginal_price_t_1w = network.buses_t.marginal_price.resample('1W')
    marginal_price_t_1M = network.buses_t.marginal_price.resample('1ME')

    for bus in buses:
        bus_path = data_path / 'buses' / bus
        bus_path.mkdir(parents=True, exist_ok=True)
        marginal_price_t_3h[bus].to_csv(bus_path / 'marginal_price_t_3h.csv')
        marginal_price_t_1d[bus].to_csv(bus_path / 'marginal_price_t_1d.csv')
        marginal_price_t_1w[bus].to_csv(bus_path / 'marginal_price_t_1w.csv')
        marginal_price_t_1M[bus].to_csv(bus_path / 'marginal_price_t_1M.csv')
    '''

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
