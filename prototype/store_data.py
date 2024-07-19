from lib.optimize import create_and_store_optimize
from lib.network import create_and_store_network
from lib.costs import create_and_store_costs
from lib.cutout import create_and_store_cutout
from lib.availability import create_and_store_availability
from lib.demand import create_and_store_demand
from lib.analytics import create_and_store_data_analytics
from lib.tools import clear_files_not_needed_for_dashboard_for_config

def store_data(config, for_dashboard):

    # Files: costs.csv
    #create_and_store_costs(config)

    # Files: cutout.nc, time_index.csv, selection.shp (incl .cpg, .dbf, .prj, .shx), eez.shp (incl .cpg, .dbf, .prj, .shx)
    create_and_store_cutout(config)

    # Files: avail_{solar|onwind|offwind}.nc, avail_capacity_{solar|onwind|offwind}.nc
    create_and_store_availability(config)

    # Files: demand.csv
    create_and_store_demand(config)

    # Files: network.nc
    create_and_store_network(config)

    # Files: statistics.pkl
    create_and_store_optimize(config)

    # Files: network.pkl
    create_and_store_data_analytics(config)

    if for_dashboard:
        clear_files_not_needed_for_dashboard_for_config(config)
        