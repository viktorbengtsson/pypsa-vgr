from lib.optimize import create_and_store_optimize
from lib.network import create_and_store_network
from lib.costs import create_and_store_costs
from lib.cutout import create_and_store_cutout
from lib.availability import create_and_store_availability
from lib.demand import create_and_store_demand

def store_data(config):

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
