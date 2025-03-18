import sys
import pandas as pd
import geopandas as gpd
import json
import xarray as xr
import pypsa
import shutil
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths
from model.assumptions_core import read_assumptions
from model.network_core import build_network
from model.constraints_core import calculate_biogas_max, add_self_sufficiency_constraint, add_battery_flow_constraint, add_biogas_constraint
from library.utilities import delete_file
from library.api.demand_core import create_and_store_demand
from library.api.converters_core import create_and_store_links
from library.api.generators_core import create_and_store_generators
from library.api.stores_core import create_and_store_stores
from library.api.performance_core import create_and_store_performance_metrics, create_and_store_sufficiency
from library.api.price_core import create_and_store_lcoe
from library.api.addon_landuse import select_and_store_land_use
from input.geo.geo_core import get_geo

# CORE
# Test that the default get_geo function has been replaced
def check_get_geo_function(config):
    geo = get_geo(config)
    if geo['weather'] == '' or geo['section'] == '':
        print("The default get_geo function has not been replaced")

# CORE
# Process assumptions csv to dataframe and save csv
def create_and_store_parameters(config):
    data_path = paths.api_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (data_path / 'assumptions.csv').is_file():
        print("assumptions.csv already exists, continue")
        return

    assumptions = read_assumptions(paths.input_root / 'assumptions.csv', 
                                   config["base-year"], config["scenario"]["target-year"], config["base-currency"], config["exchange-rates"], config["discount-rate"]
                                   )
    assumptions.to_csv(data_path / 'assumptions.csv.gz', compression='gzip')
    
    if not (paths.api_path / f'assumptions,target-year={config["scenario"]["target-year"]}.csv.gz').is_file():
        assumptions.to_csv(paths.api_path / f'assumptions,target-year={config["scenario"]["target-year"]}.csv.gz', compression='gzip')

# CORE
# Check that weather files exist (if not see /input/weather/generate-weather.ipynb)
def check_weather_files(config):
    geo = get_geo(config)

    cutout_files = list(paths.weather.glob(f"cutout,geography={geo['weather']},start=*.nc"))
    selection_files = list(paths.weather.glob(f"selection,geography={geo['section']},start=*.shp"))
    index_files = list(paths.weather.glob(f"index,geography={geo['weather']},start=*.csv"))

    if not (len(cutout_files) > 0 and len(selection_files) > 0 and len(index_files) > 0):
        print(f"Weather files do not exist for geography weather={geo['weather']}, section={geo['section']}. Please see /input/weather/generate-weather.ipynb")

# CORE
# Check that renewables files exist (if not see /input/renewables/generate-renewables.ipynb)
def check_renewables_files(config):
    geo = get_geo(config)

    avail_matrix_files = list(paths.renewables.glob(f"availability-matrix,geography={geo['section']},start=*.nc"))    
    cap_fac_files = list(paths.renewables.glob(f"capacity-factor,geography={geo['section']},start=*.nc"))    

    if not (len(avail_matrix_files) > 0 and len(cap_fac_files) > 0):
        print(f"Renewables files do not exist for geography {geo['section']}. Please see /input/renewables/generate-renewables.ipynb")

# CORE
# Copy demand/load time series
def create_and_store_demand_input(config):
    data_path = paths.api_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)
    geo = get_geo(config)
    energy_scenario_type = config['energy-scenario-type']
    energy_scenario = config['scenario']['energy-scenario']

    if (data_path / 'demand.csv.gz').is_file():
        print("Demand series already exists, continue")
        return
    
    # Build file name of projected-demand file --> read the file --> adjust to scenario
    if energy_scenario_type == "fixed":
        projected_demand = f"normalized-demand.csv"
        demand = pd.read_csv(paths.demand / projected_demand, index_col = 0)
        demand = demand * energy_scenario
    else:
        projected_demand = f"projected-demand,geography={geo['section']},target-year={config['scenario']['target-year']},growth-only={config['demand']['growth-only']}.csv.gz"
        demand = pd.read_csv(paths.demand / projected_demand, index_col = 0, compression='gzip')
        demand = demand * (1 + energy_scenario)

    # Write to file
    demand.to_csv(data_path / 'demand.csv.gz', compression='gzip')

# CORE
# Create and store the pypsa network
def create_and_store_network(config):
    data_path = paths.api_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (data_path / 'network.nc').is_file():
        print("Network already exists, continue")
        return

    # Load weather data config
    with (paths.geo_root / 'config.json').open('r') as f:
        weather_config = json.load(f)

    geo = get_geo(config)

    resolution = 3
    index = pd.to_datetime(pd.read_csv(paths.weather / f"index,geography={geo['weather']},start={weather_config['weather-start']},end={weather_config['weather-end']}.csv")['0'])
    geography = gpd.read_file(paths.weather / f"selection,geography={geo['section']},start={weather_config['weather-start']},end={weather_config['weather-end']}.shp").total_bounds
    demand = pd.read_csv(data_path / 'demand.csv.gz', index_col=0, compression='gzip').values.flatten()
    assumptions = pd.read_csv(data_path / 'assumptions.csv.gz', compression='gzip', index_col=[0,1])

    capacity_factor_solar = xr.open_dataarray(paths.renewables / f"capacity-factor-solar,geography={geo['section']},start={weather_config['weather-start']},end={weather_config['weather-end']}.nc").values.flatten()
    capacity_factor_onwind = xr.open_dataarray(paths.renewables / f"capacity-factor-onwind,geography={geo['section']},start={weather_config['weather-start']},end={weather_config['weather-end']}.nc").values.flatten()
    capacity_factor_offwind = xr.open_dataarray(paths.renewables / f"capacity-factor-offwind,geography={geo['section']},start={weather_config['weather-start']},end={weather_config['weather-end']}.nc").values.flatten()

    #use_nuclear = bool(config['scenario']["network-nuclear"])
    self_sufficiency = config['scenario']['self-sufficiency']
    offwind = bool(config['scenario']["offwind"])
    h2 = bool(config['scenario']["h2"])
    biogas_limit = config['scenario']["biogas-limit"]
    h2_initial = config['h2-initial']
    discount_rate = config['discount-rate']

    print(f"Using config:\n\tself-sufficiency:{self_sufficiency}\n\th2:{h2}\n\toffwind:{offwind}\n\tbiogas:{biogas_limit}")

    biogas = calculate_biogas_max(biogas_limit, demand, assumptions.loc['combined_cycle_gas_turbine','efficiency'].value, "average")

    network = build_network(index, resolution, geography, demand, assumptions, discount_rate, capacity_factor_solar, capacity_factor_onwind, capacity_factor_offwind, offwind, h2, h2_initial, biogas)

    network.export_to_netcdf(data_path / 'network.nc')

# CORE
# Run optimization and store results
def create_and_store_optimize(config):
    data_path = paths.api_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')
    model = network.optimize.create_model()

    ## Add constraints
    add_self_sufficiency_constraint(model, network.loads_t.p_set['load'].values, config['scenario']['self-sufficiency'])
    add_battery_flow_constraint(model, network.links.at["battery-charge", "efficiency"])
    add_biogas_constraint(model, network.loads_t.p_set['load'].values, config['scenario']['biogas-limit'], network.links.at["gas-turbine", "efficiency"])

    # Run optimization
    network.optimize.solve_model(solver_name='highs')

    # Save results
    network.export_to_netcdf(data_path / 'network.nc')

# CORE
# Write files to the API folder
def create_and_store_results(config):
    data_path = paths.api_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (paths.api_path / 'config.json').is_file():
        print("Results files already exist, continue")
        return

    # Load the results from the pypsa network
    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')

    geo = config["scenario"]["geography"]
    use_offwind = bool(config["scenario"]["offwind"])
    use_h2 = bool(config['scenario']['h2'])
    use_biogas = config['scenario']['biogas-limit'] > 0
    gas_turbine_efficiency = network.links.loc['gas-turbine', 'efficiency'] if use_biogas else 0

    resolution = 3

    ## Copy config and general assumptions to api
    shutil.copy(paths.generator_path / 'configs' / f"{config['config-name']}.json", paths.api_path / 'scenarios.json')
    shutil.copy(paths.input_root / 'assumptions.csv', paths.api_path / 'assumptions.csv')
    shutil.copy(paths.geo_root / 'markanvandning.csv.gz', paths.api_path / 'markanvandning.csv.gz')
    
    ## Create and store core API files
    create_and_store_demand(data_path / 'demand.csv.gz', data_path / 'demand', resolution)
    create_and_store_links(data_path / 'converters', use_h2, use_biogas, network.links, network.links_t, resolution)
    create_and_store_generators(data_path / 'generators', use_offwind, use_h2, use_biogas, network.generators, network.generators_t, network.links, network.links_t, gas_turbine_efficiency, resolution)
    create_and_store_stores(data_path / 'stores', use_offwind, use_h2, network.stores, network.stores_t.p, network.links, network.links_t, network.loads_t, network.generators_t, gas_turbine_efficiency, resolution)
    create_and_store_sufficiency(data_path / 'performance', network.generators_t.p['backstop'], network.generators_t.p['market'], network.loads_t.p, resolution)
    create_and_store_performance_metrics(data_path / 'performance', use_offwind, network.generators, network.generators_t, network.loads_t.p, resolution)
    create_and_store_lcoe(data_path / 'price', use_offwind, use_h2, use_biogas, network.generators, network.generators_t.p, network.links, network.links_t, network.stores, resolution)

    ## Create overall network data
    ''' FOR SOME REASON WE ARE NOT GETTING MARGINAL_PRICES FROM THE MODEL. NEED TO INVESTIGATE THIS.
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

    ## Create and store addon API files
    ## Select and store land use data (Specific to VGR application)
    # select_and_store_land_use(paths.input_root / 'geo', 'markanvandning.csv.gz', data_path, geo)


# CORE
# Clear working files not needed in API
def clear_working_files(config):
    data_path = paths.api_path / config['scenario']['data-path']
    delete_file(data_path / 'demand.csv.gz')
    delete_file(data_path / 'network.nc')
