import pandas as pd
import os.path

def create_and_store_costs(config):
    scenario_config=config["scenario"]
    year = scenario_config["costs"]

    DATA_ROOT_PATH="data/result"
    YEAR_KEY = f"{year}"
    DATA_PATH = f"{DATA_ROOT_PATH}/{YEAR_KEY}"

    if os.path.isfile(f"../{DATA_PATH}/costs.pkl"):
        print("Costs: Files already exists, continue")
        return
    if not os.path.exists(f"../{DATA_PATH}"):
        os.makedirs(f"../{DATA_PATH}")

    assumptions = pd.read_csv(f"../data/techdata/costs_{year}.csv", index_col=list(range(2))).sort_index()
    assumptions.loc[assumptions.unit.str.contains("/kW"),"value"]*=1e3
    assumptions.loc[assumptions.unit.str.contains("EUR"),"value"]*=config["eur_to_sek"]
    assumptions.to_pickle(f"../{DATA_PATH}/costs.pkl")
