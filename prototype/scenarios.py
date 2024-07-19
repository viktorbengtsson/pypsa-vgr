import sys
import json
import time
import os.path
import shutil
import itertools
from pathlib import Path
from store_data import store_data
from lib.tools import clear_files_not_needed_for_dashboard

def load_config_scenarios(scenarios, category=None):
    combinations = []
    keys = []
    for key in scenarios:
        value = scenarios[key]
        scenario_key = key if category is None else f"{category}-{key}"
        if isinstance(value, str):
            raise Exception(f"Scenarios configuration must either be a list or an object where each property is a list. {key} is a string.")
        elif isinstance(value, int) or isinstance(value, float):
            raise Exception(f"Scenarios configuration must either be a list or an object where each property is a list. {key} is a number.")
        elif isinstance(value, list):
            keys.append({ "code": scenario_key, "is_empty": len(value) == 0 })
            if len(value) > 0:
                for check in value:
                    if not (isinstance(check, int) or isinstance(check, float) or isinstance(check, str)):
                        raise Exception(f"Scenarios configuration values (in a list) must be either number or string: Value {check} in {scenario_key} is a {type(check)}.")
                combinations.append(value)
        else:
            if category is not None:
                raise Exception(f"Scenarios configuration must either be a list or an object where each property is a list. The level for {key} is too deep.")
            [more_combinations, more_keys] = load_config_scenarios(value, category=key)
            if len(more_combinations) > 0:
                combinations.extend(more_combinations)
            if len(more_keys) > 0:
                keys.extend(more_keys)
    return [combinations, keys]

def load_config(root, config_name, action = None):
    with open(f"{root}/configs/{config_name}.json", "r") as f:
        config = json.load(f)

    [combinations, keys] = load_config_scenarios(config.pop("scenarios", None))
    scenarios = list(itertools.product(*combinations))

    if action == "create":
        print(f"Creating data for all {len(scenarios)} scenarios using following configuration from ({config_name}.json):")
        for key in config:
            print(f"  {key}: {config[key]}")
        print("")

    return [config, scenarios, keys]

def create_scenario_key(config, scenario, keys):
    unique_key = ""
    for item in keys:
        code = item["code"]
        prop = "None" if bool(item["is_empty"]) else f"{{{code}}}"
        unique_key = f"{unique_key},{code}={prop}"

    unique_key = unique_key.strip(",")
    existing_keys = list(filter(lambda item: not item["is_empty"], keys))

    scenario = dict((existing_keys[i]["code"], x) for i, x in enumerate(scenario))
    return [unique_key.format(**scenario), scenario]

def create_scenario(config, scenario, keys, for_dashboard):
    [unique_key, scenario] = create_scenario_key(config, scenario, keys)
    
    folder = f"data/result/{unique_key}"
    result_folder = f"result/{unique_key}"

    config["scenario"] = scenario
    config["scenario"]["data-path"] = result_folder

    config["scenario"]["geography_lan_code"] = config["scenario"]["geography"].split(":")[0]
    config["scenario"]["geography_kom_code"] = config["scenario"]["geography"].split(":")[1] if ":" in config["scenario"]["geography"] else None

    weather_year = config["scenario"]["weather"]
    config["scenario"]["weather_start"] = f"{weather_year}-01"
    config["scenario"]["weather_end"] = f"{weather_year}-12"

    Path(f"../{folder}").mkdir(parents=True, exist_ok=True)
    with open(f"../{folder}/config.json", "w") as fp:
        json.dump(config, fp, indent=4)

    store_data(config, for_dashboard)

if __name__ == "__main__":
    action = str(sys.argv[1])
    config_name = str(sys.argv[2])
    run_mode = str(sys.argv[3])
    selected_unique_key = None if len(sys.argv) < 5 else str(sys.argv[4])
    [config, scenarios, keys] = load_config(".", config_name, action)

    if len(scenarios) > 10000:
        raise Exception(f"Exceeded maximum number for scenarios (1000): {len(scenarios)}")

    if run_mode == "True" or run_mode == "dashboard":
        print("Clear result folder")
        folder = "../data/result/"
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    start_time = time.time()
    found = False
    for idx, scenario in enumerate(scenarios):
        if action == "create":
            create_scenario(config, scenario, keys, run_mode == "dashboard")
            print(f"{idx+1} out of {len(scenarios)}: {scenario}")
        if action == "list":
            [unique_key, _] = create_scenario_key(config, scenario, keys)
            print(unique_key)
        if action == "validate":
            [unique_key, _] = create_scenario_key(config, scenario, keys)
            if selected_unique_key == unique_key:
                found = True
                break

    if action == "create" and run_mode == "dashboard":
        print("Clear data shared by all scenarios")
        clear_files_not_needed_for_dashboard()

    if action == "create":
        print("Execution time: %.4f minutes" % ((time.time() - start_time) / 60))

    if action == "validate":
        if not found:
            raise Exception(f"Scenario {selected_unique_key} could not be found in configuration {config_name}.json")
        for fname in [f"../data/result/{selected_unique_key}/{{key}}".format(key=file) for file in ["config.json"]]:
            if not os.path.isfile(fname):
                raise Exception(f"Missing scenario file: {fname}. \n\nPlease run following command to create files: %run scenarios.py \"create\" \"{config_name}\"")
