import pandas as pd
import geopandas as gpd
import xarray as xr
import pypsa


def create_and_store_network(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    TARGET_LOAD=scenario_config["load-target"]
    ASSUMPTIONS = pd.read_pickle(f"../{DATA_PATH}/costs.pkl")
    
    SELECTION = gpd.read_file(f"../{DATA_PATH}/selection.shp")
    INDEX = pd.to_datetime(pd.read_csv(f"../{DATA_PATH}/time_index.csv")["0"])
    
    AVAIL_CAPACITY_SOLAR = xr.open_dataarray(f"../{DATA_PATH}/avail_capacity_solar.nc")
    AVAIL_CAPACITY_ONWIND = xr.open_dataarray(f"../{DATA_PATH}/avail_capacity_onwind.nc")
    AVAIL_CAPACITY_OFFWIND = xr.open_dataarray(f"../{DATA_PATH}/avail_capacity_offwind.nc")

    NULL_CAPACITY = [0] * len(INDEX)

    nuclear = bool(scenario_config["network-nuclear"])
    h2 = bool(scenario_config["network-h2"])
    biogas = str(scenario_config["network-biogas"]) # Ingen, Liten, Mellan, Stor

    print(f"Using config:\n\th2:{h2}\n\tnuclear:{nuclear}\n\tbiogas:{biogas}")

    # Build and visualize the network
    
    """
    The network:
    
    A central bus that connects a solar generator, an onshore and an offshore wind generator, a battery, and a load.
    
    """
    
    ## Initialize the network
    network = pypsa.Network()
    network.set_snapshots(INDEX)
    
    ## Carriers
    carriers = [
        "onwind",
        "offwind",
        "solar",
        "battery storage",
        "market",
        ]
    
    network.madd(
        "Carrier",
        carriers,
        color=["dodgerblue", "aquamarine", "gold", "indianred", "magenta"], #, "yellowgreen"],
        )
    
    ## Main bus location
    minx, miny, maxx, maxy = SELECTION.total_bounds
    midx = (minx + maxx)/2
    midy = (miny + maxy)/2
    
    ## Add the buses
    network.add("Bus", "Main bus", x=midx, y=midy)
    network.add("Bus", "Solar bus", x=midx+0.5, y=midy+0.25)
    network.add("Bus", "Onwind bus", x=midx+0.5, y=midy-0.15)
    network.add("Bus", "Offwind bus", x=midx-1.25, y=midy-0.75)
    network.add("Bus", "Battery bus", x=midx-0.5, y=midy)
    # network.add("Bus", "H2 bus", x=midx-0.3, y=midy+0.4)
    network.add("Bus", "Market bus", x=15, y=62)
    
    ## Add loads
    network.add("Load", "Desired load", bus="Main bus",
                p_set=TARGET_LOAD
                )
    
    ## Add generators
    network.add("Generator", "Solar park", carrier="solar", bus="Solar bus",
                p_nom_extendable=True, 
                # OBS OBS OBS                ! Using nuclear variable as example for solar
                p_max_pu=AVAIL_CAPACITY_SOLAR.values.flatten() if nuclear else NULL_CAPACITY,
                capital_cost=ASSUMPTIONS.loc['solar-utility','investment'].value,
                )
    
    network.add("Link", "Solar link",
                bus0="Solar bus",
                bus1="Main bus",
                p_nom_extendable=True,
                )
    
    network.add("Generator", "Wind farm onshore", carrier="onwind", bus="Onwind bus",
                p_max_pu=AVAIL_CAPACITY_ONWIND.values.flatten(),
                capital_cost=ASSUMPTIONS.loc['onwind','investment'].value,
                )
    
    network.add("Link", "Onwind link",
                bus0="Onwind bus",
                bus1="Main bus",
                p_nom_extendable=True,
                )
    
    network.add("Generator", "Wind farm offshore", carrier="offwind", bus="Offwind bus",
                p_nom_extendable=True, 
                p_max_pu=AVAIL_CAPACITY_OFFWIND.values.flatten(),
                capital_cost=ASSUMPTIONS.loc['offwind','investment'].value,
                )
    
    network.add("Link", "Offwind link",
                bus0="Offwind bus",
                bus1="Main bus",
                p_nom_extendable=True,
                )
    
    ## Add battery storage TODO: experiment with replacing this with just a normal store and see the effect
    network.add("Store", "Battery", carrier="battery storage", bus="Battery bus",
                e_nom_extendable=True,
                e_cyclic=True,
                #state_of_charge_initial=10,
                capital_cost=ASSUMPTIONS.loc["battery storage", "investment"].value,
                )
    
    network.add("Link","Battery charge",
                    bus0 = "Main bus",
                    bus1 = "Battery bus",
                    efficiency = ASSUMPTIONS.loc['battery inverter','efficiency'].value,
                    p_nom_extendable = True,
                    capital_cost=ASSUMPTIONS.loc['battery inverter','investment'].value,
                    )
    
    network.add("Link","Battery discharge",
                    bus0 = "Battery bus",
                    bus1 = "Main bus",
                    efficiency = ASSUMPTIONS.loc['battery inverter','efficiency'].value,
                    p_nom_extendable = True,
                    )
    
    ## Add market (incl. existing production)
    network.add("Load", "Market consumption", bus="Market bus",
                p_set=15000
                )
    
    network.add("Generator", "Market production", carrier="market", bus="Market bus",
                p_nom=15000
                )
    
    network.add("Link","Sell to market",
                    bus0 = "Main bus",
                    bus1 = "Market bus",
                    p_nom_extendable = True,
                    marginal_cost=-3000
                    )
    
    network.add("Link","Buy from market",
                    bus0 = "Market bus",
                    bus1 = "Main bus",
                    p_nom_extendable = True,
                    marginal_cost=3000+300
                    )

    network.export_to_netcdf(f"../{DATA_PATH}/network.nc")
