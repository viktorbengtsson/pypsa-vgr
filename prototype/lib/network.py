import pandas as pd
import geopandas as gpd
import xarray as xr
import pypsa
import pickle
import os.path

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
    
    SELECTION = gpd.read_file(f"../{GEO_DATA_PATH}/selection.shp")
    INDEX = pd.to_datetime(pd.read_csv(f"../{GEO_DATA_PATH}/time_index.csv")["0"])
    
    AVAIL_CAPACITY_SOLAR = xr.open_dataarray(f"../{GEO_DATA_PATH}/avail_capacity_solar.nc")
    AVAIL_CAPACITY_ONWIND = xr.open_dataarray(f"../{GEO_DATA_PATH}/avail_capacity_onwind.nc")
    AVAIL_CAPACITY_OFFWIND = xr.open_dataarray(f"../{GEO_DATA_PATH}/avail_capacity_offwind.nc")

    LOAD = pd.read_csv(f"../{DEMAND_DATA_PATH}/demand.csv")["se3"].values.flatten()

    NULL_CAPACITY = [0] * len(INDEX)
    RESOLUTION = 3 #3h window for weather data and pypsa model optimization
    parameters = pd.read_csv("../data/assumptions.csv")
    parameters.set_index(['technology', 'parameter'], inplace=True)

    use_nuclear = bool(scenario_config["network-nuclear"])
    use_offwind = bool(scenario_config["network-offwind"])
    use_h2 = bool(scenario_config["network-h2"])
    biogas_profile = str(scenario_config["network-biogas"]) # Ingen, Liten, Mellan, Stor

    biogas_production_max_nominal = config["profiles"]["biogas"][biogas_profile]

    print(f"Using config:\n\th2:{use_h2}\n\tnuclear:{use_nuclear}\n\toffwind:{use_offwind}\n\tbiogas:{biogas_profile}")

    def annuity(r, n):
        return r / (1.0 - 1.0 / (1.0 + r) ** n)
    
    def annualized_capex(asset):
        return (annuity(float(parameters.loc[('general', 'discount_rate'), 'value']), float(parameters.loc[(asset, 'lifetime'), 'value'])) + float(parameters.loc[(asset, 'FOM'), 'value'])) * float(parameters.loc[(asset, 'capital_cost'), 'value'])

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
        'mixedgas',
        'backstop',
        'nuclear',
        ]

    carrier_colors = ['black', 'green', 'blue', 'red', 'lightblue', 'grey', 'brown', 'brown', 'white', 'mintgreen']

    network.madd(
        'Carrier',
        carriers,
        color=carrier_colors,
        )

    ## Load bus location
    minx, miny, maxx, maxy = SELECTION.total_bounds
    midx = (minx + maxx)/2
    midy = (miny + maxy)/2

    ## Add the buses
    network.add('Bus', 'Load bus', carrier='AC', x=midx, y=midy)
    network.add('Bus', 'Solar', x=midx+0.5, y=midy+0.25)
    network.add('Bus', 'Onwind', x=midx+0.5, y=midy-0.15)
    network.add('Bus', 'Offwind', x=midx-1.25, y=midy-0.75)
    network.add('Bus', 'Battery bus', carrier='li-ion', x=midx-0.5, y=midy)
    network.add('Bus', 'Battery storage', carrier='li-ion', x=midx-0.5, y=midy)
    network.add('Bus', 'Gas turbine', x=midx, y=midy+0.5)
    network.add('Bus', 'H2 bus', carrier='h2', x=midx-0.5, y=midy+0.5)
    network.add('Bus', 'H2 storage', carrier='h2', x=midx-0.5, y=midy+0.5)
    network.add('Bus', 'Biogas market', x=midx, y=midy+0.9)
    network.add('Bus', 'Nuclear', carrier='nuclear', x=midx, y=midy+0.9)
    

    ## Add loads
    network.add('Load', 'Desired load', bus='Load bus',
                p_set=LOAD
                )

    network.add('Generator', 'Backstop', carrier='backstop', bus='Load bus',
                p_nom_extendable=True,
                capital_cost=parameters.loc[('backstop', 'capital_cost'), 'value'],
                marginal_cost=parameters.loc[('backstop', 'marginal_cost'), 'value'],
                lifetime=parameters.loc[('backstop', 'lifetime'), 'value'],
                )

    ## Add generators

    ### Solar
    network.add('Generator', 'Solar park', carrier='solar', bus='Solar',
                p_nom_extendable=True, 
                p_max_pu=AVAIL_CAPACITY_SOLAR.values.flatten(),
                p_nom_mod=parameters.loc['solar','unit_size'].value,
                capital_cost= annualized_capex('solar'),
                marginal_cost=parameters.loc[('solar', 'VOM'), 'value'],
                lifetime=parameters.loc[('solar', 'lifetime'), 'value'],
                )

    network.add('Link', 'Solar load link', carrier='solar', bus0='Solar', bus1='Load bus',
                p_nom_extendable=True,
                )

    network.add('Link', 'Solar battery link', carrier='solar', bus0='Solar', bus1='Battery bus',
                p_nom_extendable=True,
                )

    network.add('Link', 'Solar H2 link', carrier='solar', bus0='Solar', bus1='H2 bus',
                p_nom_extendable=True,
                )

    ### Onwind
    network.add('Generator', 'Onwind park', carrier='onwind', bus='Onwind',
                p_nom_extendable=True,
                p_max_pu=AVAIL_CAPACITY_ONWIND.values.flatten(),
                p_nom_mod=parameters.loc['onwind','unit_size'].value,
                capital_cost= annualized_capex('onwind'),
                marginal_cost=parameters.loc[('onwind', 'VOM'), 'value'],
                lifetime=parameters.loc['onwind','lifetime'].value,
                )

    network.add('Link', 'Onwind load link', carrier='onwind', bus0='Onwind', bus1='Load bus',
                p_nom_extendable=True,
                )

    network.add('Link', 'Onwind battery link', carrier='onwind', bus0='Onwind', bus1='Battery bus',
                p_nom_extendable=True,
                )

    network.add('Link', 'Onwind H2 link', carrier='onwind', bus0='Onwind', bus1='H2 bus',
                p_nom_extendable=True,
                )

    ### Offwind
    network.add('Generator', 'Offwind park', carrier='offwind', bus='Offwind',
                p_nom_extendable=use_offwind,
                p_max_pu=(AVAIL_CAPACITY_OFFWIND.values.flatten() if use_offwind else [0] * len(AVAIL_CAPACITY_OFFWIND.values.flatten())),
                p_nom_mod=parameters.loc['offwind','unit_size'].value,
                capital_cost= annualized_capex('offwind'),
                marginal_cost=parameters.loc[('offwind', 'VOM'), 'value'],
                lifetime=parameters.loc['offwind','lifetime'].value,
                )

    network.add('Link', 'Offwind load link', carrier='offwind', bus0='Offwind', bus1='Load bus',
                p_nom_extendable=use_offwind,
                )

    network.add('Link', 'Offwind battery link', carrier='offwind', bus0='Offwind', bus1='Battery bus',
                p_nom_extendable=use_offwind,
                )

    network.add('Link', 'Offwind H2 link', carrier='offwind', bus0='Offwind', bus1='H2 bus',
                p_nom_extendable=use_offwind,
                )

    ## Add H2 electrolysis, storage, pipline to gas turbine

    network.add('Link', 'toH2', bus0='Load bus', bus1='H2 bus',
                p_nom_extendable=True
                )

    network.add('Link', 'H2 electrolysis', carrier='h2', bus0='H2 bus', bus1='H2 storage',
                p_nom_extendable=True,
                p_nom_mod=parameters.loc['h2_electrolysis','unit_size'].value,
                capital_cost= annualized_capex('h2_electrolysis'),
                marginal_cost=parameters.loc[('h2_electrolysis', 'VOM'), 'value'],
                lifetime=parameters.loc['h2_electrolysis','lifetime'].value,
                efficiency=parameters.loc['h2_electrolysis','efficiency'].value,
                )

    network.add('Store', 'H2 storage', carrier='h2', bus='H2 storage',
                e_initial=(150_000 if use_h2 else 0),
                e_nom_extendable=use_h2,
                e_cyclic=True,
                capital_cost= annualized_capex('h2_storage'),
                marginal_cost=parameters.loc['h2_storage','VOM'].value,
                lifetime=parameters.loc['h2_storage','lifetime'].value
                )

    network.add('Link', 'H2 pipeline', carrier='h2', bus0='H2 storage', bus1='Gas turbine',
                p_nom_extendable=True,
                )

    ### Biogas pipeline

    network.add('Generator', 'Biogas input', carrier='biogas', bus='Biogas market',
                p_nom_extendable=True,
                p_nom_max=biogas_production_max_nominal,
                marginal_cost=parameters.loc['biogas','cost'].value,
                lifetime=100,
                )

    network.add('Link', 'Biogas pipeline', carrier='biogas', bus0='Biogas market', bus1='Gas turbine',
                p_nom_extendable=True,
                )

    ### Gas turbines
    network.add('Link', 'Simple Cycle Gas turbine', carrier='mixedgas', bus0='Gas turbine', bus1='Load bus',
                p_nom_extendable=True,
                p_nom_mod=parameters.loc['simple_cycle_gas_turbine','unit_size'].value,
                capital_cost= annualized_capex('simple_cycle_gas_turbine'),
                marginal_cost=parameters.loc['simple_cycle_gas_turbine','VOM'].value,
                lifetime=parameters.loc['simple_cycle_gas_turbine','lifetime'].value,
                efficiency=parameters.loc['simple_cycle_gas_turbine','efficiency'].value,
                )

    network.add('Link', 'Combined Cycle Gas turbine', carrier='mixedgas', bus0='Gas turbine', bus1='Load bus',
                p_nom_extendable=True,
                p_nom_mod=parameters.loc['combined_cycle_gas_turbine','unit_size'].value,
                capital_cost= annualized_capex('combined_cycle_gas_turbine'),
                marginal_cost=parameters.loc['combined_cycle_gas_turbine','VOM'].value,
                lifetime=parameters.loc['combined_cycle_gas_turbine','lifetime'].value,
                efficiency=parameters.loc['combined_cycle_gas_turbine','efficiency'].value,
                )

    ## Add battery storage

    network.add('Link', 'toBattery', carrier='li-ion', bus0='Load bus', bus1='Battery bus',
                p_nom_extendable=True
                )

    network.add('Link','Battery charge', bus0 = 'Battery bus', bus1 = 'Battery storage',
                p_nom_extendable = True,
                capital_cost= annualized_capex('battery_inverter'),
                marginal_cost=parameters.loc['battery_inverter','VOM'].value,
                lifetime=parameters.loc['battery_inverter','lifetime'].value,
                efficiency = parameters.loc['battery_inverter','efficiency'].value,
                )

    network.add('Store', 'Battery storage', carrier='li-ion', bus='Battery storage',
                e_initial=100,
                e_nom_extendable=True,
                e_cyclic=True,
                e_min_pu=0.15,
                standing_loss=0.00008, # TODO: Check if this is really per hour as in the documentation or if it is per snapshot
                capital_cost= annualized_capex('battery_storage'),
                marginal_cost=parameters.loc['battery_storage','VOM'].value,
                lifetime=parameters.loc['battery_storage', 'lifetime'].value,
                )

    network.add('Link','Battery discharge', carrier='li-ion', bus0 = 'Battery storage', bus1 = 'Load bus',
                p_nom_extendable = True,
                efficiency = parameters.loc['battery_inverter','efficiency'].value,
                )

    ## Nuclear
    num_nuclear_conv = 0 if use_nuclear else 0
    num_nuclear_smr = 2 if use_nuclear else 0

#       for i in range(num_nuclear_conv):
    network.add('Generator', f"{'Conventional nuclear'}", carrier='nuclear', bus='Nuclear',
            p_nom_extendable=True,
            p_nom_mod=parameters.loc['nuclear_conv','p_nom'].value,
            p_nom_max=num_nuclear_conv * float(parameters.loc['nuclear_conv','p_nom'].value),
#                p_nom=parameters.loc['nuclear_conv','p_nom'].value,
            capital_cost= annualized_capex('nuclear_conv'),
            marginal_cost=float(parameters.loc['nuclear_conv','VOM'].value) + float(parameters.loc['nuclear_conv','fuel'].value),
            lifetime=parameters.loc['nuclear_conv','lifetime'].value,
            )

#        for j in range(num_nuclear_smr):
    network.add('Generator', f"{'SMR nuclear'}", carrier='nuclear', bus='Nuclear',
            p_nom_extendable=True,
            p_nom_mod=parameters.loc['nuclear_smr','p_nom'].value,
            p_nom_max=num_nuclear_smr * float(parameters.loc['nuclear_smr','p_nom'].value),
#                p_nom=parameters.loc['nuclear_smr','p_nom'].value,
            capital_cost= annualized_capex('nuclear_smr'),
            marginal_cost=float(parameters.loc['nuclear_smr','VOM'].value) + float(parameters.loc['nuclear_smr','fuel'].value),
            lifetime=parameters.loc['nuclear_smr','lifetime'].value,
            )

    network.add('Link', 'Nuclear to load', carrier='nuclear', bus0='Nuclear', bus1='Load bus',
            p_nom_extendable=True,
            )

    network.export_to_netcdf(f"../{DATA_PATH}/network.nc")
