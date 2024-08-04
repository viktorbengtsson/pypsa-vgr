from lib.tools import clear_files_not_needed_for_dashboard_for_config
from lib.create_files import create_and_store_parameters, create_and_store_cutout, create_and_store_availability, create_and_store_demand, create_and_store_network, create_and_store_optimize, create_and_store_data_analytics, copy_input_data

def store_data(config, for_dashboard, config_name):

    # Files: costs.csv
    create_and_store_parameters(config)

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

    # Input data that is also needed for output
    copy_input_data(config_name)

    if for_dashboard:
        clear_files_not_needed_for_dashboard_for_config(config)
        