import pypsa

def create_and_store_optimize(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"../{DATA_PATH}/network.nc")

    NETWORK.optimize()
    statistics = NETWORK.statistics()
    statistics.to_pickle(f"../{DATA_PATH}/statistics.pkl")

