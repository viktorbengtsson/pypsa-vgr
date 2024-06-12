import pandas as pd
import geopandas as gpd
import xarray as xr
import pypsa
import pickle

def create_and_store_network(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    ASSUMPTIONS = pd.read_pickle(f"../{DATA_PATH}/costs.pkl")
    
    SELECTION = gpd.read_file(f"../{DATA_PATH}/selection.shp")
    INDEX = pd.to_datetime(pd.read_csv(f"../{DATA_PATH}/time_index.csv")["0"])
    
    AVAIL_CAPACITY_SOLAR = xr.open_dataarray(f"../{DATA_PATH}/avail_capacity_solar.nc")
    AVAIL_CAPACITY_ONWIND = xr.open_dataarray(f"../{DATA_PATH}/avail_capacity_onwind.nc")
    AVAIL_CAPACITY_OFFWIND = xr.open_dataarray(f"../{DATA_PATH}/avail_capacity_offwind.nc")

    LOAD = pd.read_csv(f"../{DATA_PATH}/demand.csv")["se3"].values.flatten()

    NULL_CAPACITY = [0] * len(INDEX)
    RESOLUTION = 3 #3h window for weather data and pypsa model optimization
    parameters = pd.read_csv("../data/assumptions.csv")
    parameters.set_index(['technology', 'parameter'], inplace=True)

    use_nuclear = bool(scenario_config["network-nuclear"])
    use_h2 = bool(scenario_config["network-h2"])
    biogas_profile = str(scenario_config["network-biogas"]) # Ingen, Liten, Mellan, Stor

    biogas_production_max_nominal = config["profiles"]["biogas"][biogas_profile]

    print(f"Using config:\n\th2:{use_h2}\n\tnuclear:{use_nuclear}\n\tbiogas:{biogas_profile}")

    # Build the network

    ## Initialize the network
    network = pypsa.Network()
    network.set_snapshots(INDEX)
    network.snapshot_weightings.loc[:, :] = RESOLUTION

    ## Carriers
    carriers = [
        'AC',
        'onwind',
        'offwind',
        'solar',
        'li-ion',
        'h2',
        'biogas',
        ]

    carrier_colors = ['black', 'green', 'blue', 'red', 'lightblue', 'grey', 'brown']

    network.madd(
        'Carrier',
        carriers,
        color=carrier_colors,
        )

    ## Main bus location
    minx, miny, maxx, maxy = SELECTION.total_bounds
    midx = (minx + maxx)/2
    midy = (miny + maxy)/2

    ## Add the buses
    network.add('Bus', 'Main bus', carrier='AC', x=midx, y=midy)
    network.add('Bus', 'Solar', x=midx+0.5, y=midy+0.25)
    network.add('Bus', 'Onwind', x=midx+0.5, y=midy-0.15)
    network.add('Bus', 'Offwind', x=midx-1.25, y=midy-0.75)
    network.add('Bus', 'Battery', carrier='li-ion', x=midx-0.5, y=midy)
    network.add('Bus', 'Gas turbine', x=midx, y=midy+0.5)
    network.add('Bus', 'H2 storage', carrier='h2', x=midx-0.5, y=midy+0.5)
    network.add('Bus', 'Biogas market', x=midx, y=midy+0.9)

    ## Add loads
    network.add('Load', 'Desired load', bus='Main bus',
                p_set=LOAD
                )

    network.add('Generator', 'Backstop', carrier='AC', bus='Main bus',
                p_nom_extendable=False,
                p_set=0,
                capital_cost=parameters.loc[('backstop', 'capital_cost'), 'value'],
                marginal_cost=parameters.loc[('backstop', 'marginal_cost'), 'value'],
                lifetime=parameters.loc[('backstop', 'lifetime'), 'value'],
                )

    ## Add generators

    ### Solar
    network.add('Generator', 'Solar park', carrier='solar', bus='Solar',
                p_nom_extendable=True, 
                p_max_pu=AVAIL_CAPACITY_SOLAR.values.flatten(),
                capital_cost=parameters.loc[('solar', 'capital_cost'), 'value'],
                #marginal_cost=assumptions.loc['solar-utility','FOM'].value / 100 * assumptions.loc['solar-utility','investment'].value / (mean_solar_capacity_factor.values.flatten().sum() * 3),
                lifetime=parameters.loc[('solar', 'lifetime'), 'value'],
                )

    network.add('Link', 'Solar link',
                bus0='Solar',
                bus1='Main bus',
                p_nom_extendable=True,
                )

    ### Onwind
    network.add('Generator', 'Onwind park', carrier='onwind', bus='Onwind',
                p_nom_extendable=True,
                p_max_pu=AVAIL_CAPACITY_ONWIND.values.flatten(),
                capital_cost=parameters.loc[('onwind', 'capital_cost'), 'value'],
                #marginal_cost=assumptions.loc['onwind','VOM'].value + assumptions.loc['onwind','FOM'].value / 100 * assumptions.loc['onwind','investment'].value  / (mean_onwind_capacity_factor.values.flatten().sum() * 3),
                lifetime=parameters.loc['onwind','lifetime'].value,
                )

    network.add('Link', 'Onwind link',
                bus0='Onwind',
                bus1='Main bus',
                p_nom_extendable=True,
                )

    ### Offwind
    network.add('Generator', 'Offwind park', carrier='offwind', bus='Offwind',
                p_nom_extendable=True, 
                p_max_pu=AVAIL_CAPACITY_OFFWIND.values.flatten(),
                capital_cost=parameters.loc[('offwind', 'capital_cost'), 'value'],
                #marginal_cost=assumptions.loc['onwind','VOM'].value + assumptions.loc['offwind','FOM'].value / 100 * assumptions.loc['offwind','investment'].value  / (mean_offwind_capacity_factor.values.flatten().sum() * 3),
                lifetime=parameters.loc['offwind','lifetime'].value,
                )

    network.add('Link', 'Offwind link',
                bus0='Offwind',
                bus1='Main bus',
                p_nom_extendable=True,
                )

    ## Add H2 electrolysis, storage, pipline to gas turbine

    network.add('Link',
                'H2 electrolysis',
                bus0='Main bus',
                bus1='H2 storage',
                p_nom_extendable=True,
                efficiency=parameters.loc['h2_electrolysis','efficiency'].value,
                capital_cost=parameters.loc['h2_electrolysis','capital_cost'].value,
                #marginal_cost=230+55,
                lifetime=parameters.loc['h2_electrolysis','lifetime'].value,
                )

    network.add('Store', 'H2 storage', carrier='h2', bus='H2 storage',
                e_nom_extendable=use_h2,
                e_initial=(150_000 if use_h2 else 0),
                # e_nom_max=target_load.max()*hours_h2_storage,
                capital_cost=parameters.loc['h2_storage','capital_cost'].value,
                lifetime=parameters.loc['h2_storage','lifetime'].value
                )

    network.add('Link',
                'H2 pipeline',
                bus0='H2 storage',
                bus1='Gas turbine',
                p_nom_extendable=True,
                efficiency=parameters.loc['h2','efficiency'].value,
                )

    ### Biogas pipeline

    network.add('Generator', 'Biogas market', carrier='biogas', bus='Biogas market',
                p_nom_extendable=True,
                p_nom_max=biogas_production_max_nominal,
                marginal_cost=parameters.loc['biogas','cost'].value,
                lifetime=100,
                )

    network.add('Link', 'Biogas pipeline', bus0='Biogas market', bus1='Gas turbine',
                p_nom_extendable=True,
                efficiency=parameters.loc['biogas','efficiency'].value,
                )

    ### Gas turbine
    network.add('Link', 'Gas turbine', bus0='Gas turbine', bus1='Main bus',
                p_nom_extendable=True,
                capital_cost=parameters.loc['gas_turbine','capital_cost'].value,
                #marginal_cost=assumptions.loc['CCGT','VOM'].value,
                lifetime=parameters.loc['gas_turbine','lifetime'].value,
                )

    ## Add battery storage TODO: add running cost, 
    network.add('Store', 'Battery', carrier='li-ion', bus='Battery',
                e_nom_extendable=True,
                e_cyclic=True,
                e_min_pu=0.15,
                standing_loss=0.00008, # TODO: Check if this is really per hour as in the documentation or if it is per snapshot
                capital_cost=parameters.loc['battery_storage', 'capital_cost'].value,
                lifetime=parameters.loc['battery_storage', 'lifetime'].value,
                )

    network.add('Link','Battery charge',
                bus0 = 'Main bus',
                bus1 = 'Battery',
                efficiency = parameters.loc['battery_inverter','efficiency'].value,
                p_nom_extendable = True,
                capital_cost=parameters.loc['battery_inverter','capital_cost'].value,
                #marginal_cost=0,#assumptions.loc['battery inverter','FOM'].value / 100 * assumptions.loc['battery inverter','investment'].value,
                lifetime=parameters.loc['battery_inverter','lifetime'].value,
                )

    network.add('Link','Battery discharge',
                bus0 = 'Battery',
                bus1 = 'Main bus',
                efficiency = parameters.loc['battery_inverter','efficiency'].value,
                p_nom_extendable = True,
                )

    ## Nuclear

    network.export_to_netcdf(f"../{DATA_PATH}/network.nc")
