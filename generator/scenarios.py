import sys
import json
import time
import shutil
import itertools
from library.orchestrate import run_scenario
import paths
import os.path
from time import sleep

def _load_config_scenarios(scenarios, category=None):
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
            [more_combinations, more_keys] = _load_config_scenarios(value, category=key)
            if len(more_combinations) > 0:
                combinations.extend(more_combinations)
            if len(more_keys) > 0:
                keys.extend(more_keys)
    return [combinations, keys]

def _load_config(root, config_name, action = None):
    with open(f"{root}/configs/{config_name}.json", "r") as f:
        config = json.load(f)

    [combinations, keys] = _load_config_scenarios(config.pop("scenarios", None))
    scenarios = list(itertools.product(*combinations))

    if action == "create":
        print(f"Creating data for all {len(scenarios)} scenarios using following configuration from ({config_name}.json):")
        for key in config:
            print(f"  {key}: {config[key]}")
        print("")

    return [config, scenarios, keys]

def _create_scenario_key(scenario, keys):
    unique_key = ""
    for item in keys:
        code = item["code"]
        prop = "None" if bool(item["is_empty"]) else f"{{{code}}}"
        unique_key = f"{unique_key},{code}={prop}"

    unique_key = unique_key.strip(",")
    existing_keys = list(filter(lambda item: not item["is_empty"], keys))

    scenario = dict((existing_keys[i]["code"], x) for i, x in enumerate(scenario))
    return [unique_key.format(**scenario).replace(":", "-"), scenario]

def _create_scenario(config, scenario, keys, tidy):
    [unique_key, scenario] = _create_scenario_key(scenario, keys)

    data_path = paths.output_path / unique_key
    
    config["scenario"] = scenario
    config["scenario"]["data-path"] = unique_key

    config["scenario"]["geography_lan_code"] = config["scenario"]["geography"].split(":")[0]
    config["scenario"]["geography_kom_code"] = config["scenario"]["geography"].split(":")[1] if ":" in config["scenario"]["geography"] else None

    if os.path.isfile(data_path / 'config.json'):
        print(f"{data_path}/config.json already exists")
    else:
        data_path.mkdir(parents=True, exist_ok=True)
        with (data_path / 'config.json').open('w') as fp:
            json.dump(config, fp, indent=4)

        run_scenario(config, tidy)

if __name__ == "__main__":
    action = str(sys.argv[1])
    config_name = str(sys.argv[2])
    clear = str(sys.argv[3]) == 'True'
    tidy = str(sys.argv[4]) == 'True'

    [config, scenarios, keys] = _load_config(".", config_name, action)

    if len(scenarios) > 10000:
        print(f"You are about to start generating a large number of scenarios, it might take a very long long time: {len(scenarios)}")
        # Give time to stop before creating files... (30s)
        print("Will start in 30 seconds")
        sleep(10)
        print("Will start in 20 seconds")
        sleep(10)
        print("Will start in 10 seconds")
    if len(scenarios) > 50000:
        raise Exception(f"Exceeded maximum number for scenarios (50000): {len(scenarios)}")

    if clear:
        print("Clear output folder")
        for item in paths.output_path.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f'Failed to delete {item}. Reason: {e}')


    start_time = time.time()
    found = False
    for idx, scenario in enumerate(scenarios):
        if action == "create":
            _create_scenario(config, scenario, keys, tidy)
            print(f"{idx+1} out of {len(scenarios)}: {scenario}")
        if action == "list":
            [unique_key, _] = _create_scenario_key(scenario, keys, tidy)
            print(unique_key)

    if action == "create":
        print("Execution time: %.4f minutes" % ((time.time() - start_time) / 60))
