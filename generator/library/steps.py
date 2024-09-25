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
from generator.library.tools import delete_file
from generator.library.output_files import create_and_store_demand, create_and_store_links, create_and_store_generators, create_and_store_stores, create_and_store_sufficiency
from generator.library.output_files import create_and_store_performance_metrics, create_and_store_lcoe, select_and_store_land_use

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
    assumptions.to_csv(data_path / 'assumptions.csv.gz', compression='gzip')


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


# Copy demand/load time series
def create_and_store_demand_input(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (data_path / 'demand.csv.gz').is_file():
        print("Demand series already exists, continue")
        return
    
    # Build file name of projected-demand file
    projected_demand = f"projected-demand,geography={config['scenario']['geography'].replace(':','-')},target-year={config['scenario']['target-year']},growth-only={config['demand']['growth-only']}.csv.gz"
    
    # Copy to data dir
    shutil.copy(paths.input_path / 'demand' / 'geo' / projected_demand, data_path / 'demand.csv.gz')



# Build network and store in file
def biogas_max(biogas_limit, load, gas_efficiency, method):
    return np.mean(load)*biogas_limit/gas_efficiency    

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
    demand = pd.read_csv(data_path / 'demand.csv.gz', index_col=0, compression='gzip').values.flatten()
    assumptions = pd.read_csv(data_path / 'assumptions.csv.gz', compression='gzip', index_col=[0,1])

    capacity_factor_solar = xr.open_dataarray(renewables_path / f"capacity-factor-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}-solar.nc").values.flatten()
    capacity_factor_onwind = xr.open_dataarray(renewables_path / f"capacity-factor-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}-onwind.nc").values.flatten()
    capacity_factor_offwind = xr.open_dataarray(renewables_path / f"capacity-factor-{geo['section_key']}-{weather_config['weather-start']}-{weather_config['weather-end']}-offwind.nc").values.flatten()

    #use_nuclear = bool(config['scenario']["network-nuclear"])
    self_sufficiency = config['scenario']['self-sufficiency']
    offwind = bool(config['scenario']["offwind"])
    h2 = bool(config['scenario']["h2"])
    biogas_limit = config['scenario']["biogas-limit"]
    h2_initial = config['h2-initial']
    discount_rate = config['discount-rate']

    print(f"Using config:\n\th2:{h2}\n\toffwind:{offwind}\n\tbiogas:{biogas_limit}") # TODO: Update this text

    biogas = biogas_max(biogas_limit, demand, assumptions.loc['combined_cycle_gas_turbine','efficiency'].value, "average")

    network = build_network(index, resolution, geography, demand, assumptions, discount_rate, capacity_factor_solar, capacity_factor_onwind, capacity_factor_offwind, offwind, h2, h2_initial, biogas)

    network.export_to_netcdf(data_path / 'network.nc')

# Run optimization and store results
def create_and_store_optimize(config):
    data_path = paths.output_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')
    model = network.optimize.create_model()

    demand = pd.read_csv(data_path / 'demand.csv.gz', compression='gzip', index_col='timestamp')
    total_e = demand['value'].values.flatten().sum()

#    offwind = bool(config["scenario"]["offwind"])
    self_sufficiency = config['scenario']['self-sufficiency']

    ## Add self-sufficiency constraint on the import market
    market_e = model.variables['Generator-p'].loc[:,'market'].sum()
    non_sufficiency_e = total_e * (1 - self_sufficiency)
    model.add_constraints(market_e <= non_sufficiency_e, name="Self_sufficiency_constraint")
    
    ## TODO: UPDATE THIS CONSTRAINT AFTER WE GET A NEW SOLVER
    ## Offwind constraint
    #if False:
    #    generator_capacity = model.variables["Generator-p_nom"]
    #    offwind_percentage = config['offwind-ratio']
#
#        offwind_constraint = (1 - offwind_percentage) / offwind_percentage * generator_capacity.loc['offwind'] - generator_capacity.loc['onwind']
#        model.add_constraints(offwind_constraint == 0, name="Offwind_constraint")

    ## Add battery charge/discharge ratio constraint
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

    # Load the results from the pypsa network
    network = pypsa.Network()
    network.import_from_netcdf(data_path / 'network.nc')

    geo = config["scenario"]["geography"]
    use_offwind = bool(config["scenario"]["offwind"])
    use_h2 = bool(config['scenario']['h2'])
    use_biogas = config['scenario']['biogas-limit'] > 0
    gas_turbine_efficiency = network.links.loc['gas-turbine', 'efficiency'] if use_biogas else 0

    resolution = 3

    ## Copy config and assumptions to output
    shutil.copy(paths.generator_path / 'configs' / f"{config['config-name']}.json", paths.output_path / 'scenarios.json')
    shutil.copy(paths.input_path / 'assumptions.csv', paths.output_path / 'assumptions.csv')
    
    ## Create files for demand data
    create_and_store_demand(data_path / 'demand.csv.gz', data_path / 'demand', resolution)

    ## Add active links data (battery inverters, electrolysis, and gas turbines)
    create_and_store_links(data_path / 'converters', use_h2, use_biogas, network.links, network.links_t, resolution)

    ## Create generators data and curtailment data (renewable generators only)
    create_and_store_generators(data_path / 'generators', use_offwind, use_h2, use_biogas, network.generators, network.generators_t, network.links, network.links_t, gas_turbine_efficiency, resolution)

    ## Create stores data
    create_and_store_stores(data_path / 'stores', use_offwind, use_h2, network.stores, network.stores_t.p, network.links, network.links_t, network.loads_t, network.generators_t, gas_turbine_efficiency, resolution)

    ## Create sufficiency data
    create_and_store_sufficiency(data_path / 'performance', network.generators_t.p['backstop'], network.generators_t.p['market'], network.loads_t.p, resolution)

    ## Create performance metrics
    create_and_store_performance_metrics(data_path / 'performance', use_offwind, network.generators, network.generators_t, network.loads_t.p, resolution)

    ## Create LCOE data
    create_and_store_lcoe(data_path / 'price', use_offwind, use_h2, use_biogas, network.generators, network.generators_t.p, network.links, network.links_t, network.stores, resolution)

    ## Select and store land use data (Specific to VGR application)
    select_and_store_land_use(paths.input_path / 'geo', 'markanvandning.csv.gz', data_path, geo)

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
    delete_file(data_path / 'demand.csv.gz')
    delete_file(data_path / 'network.nc')
