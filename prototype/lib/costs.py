import sys
import os.path

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from library.parameters import read_assumptions

# Process assumptions csv to dataframe and save pickle
def create_and_store_parameters(config):
    base_year = config["scenario"]["base-year"]
    target_year = config["scenario"]["target-year"]

    DATA_PATH =config["scenario"]["data-path"]    
    DATA_PATH = f"data/{DATA_PATH}"

    if os.path.isfile(f"../{DATA_PATH}/costs.pkl"):
        print("Costs: Files already exists, continue")
        return
    if not os.path.exists(f"../{DATA_PATH}"):
        os.makedirs(f"../{DATA_PATH}")

    assumptions = read_assumptions(f"../data/assumptions.csv", base_year, target_year, config["base-currency"], config["exchange-rates"], config["scenario"]["discount-rate"])
    assumptions.to_pickle(f"../{DATA_PATH}/costs.pkl")