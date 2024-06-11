import pandas as pd

def create_and_store_costs(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    year = scenario_config["costs"]

    assumptions = pd.read_csv(f"../data/techdata/costs_{year}.csv", index_col=list(range(2))).sort_index()
    assumptions.loc[assumptions.unit.str.contains("/kW"),"value"]*=1e3
    assumptions.loc[assumptions.unit.str.contains("EUR"),"value"]*=config["eur_to_sek"]
    assumptions.to_pickle(f"../{DATA_PATH}/costs.pkl")
