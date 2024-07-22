import pypsa
import pickle
import os.path
import shutil
import pandas as pd

def clear_files_not_needed_for_dashboard_for_config(config):
    scenario_config=config["scenario"]

    DATA_PATH =scenario_config["data-path"]    
    DATA_PATH = f"data/{DATA_PATH}"

    paths = [
        f"../{DATA_PATH}/statistics.pkl",
        f"../{DATA_PATH}/network.nc",
    ]

    for file_path in paths:
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                print("Invalid path")
                print(os.path.abspath(file_path))
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def clear_files_not_needed_for_dashboard():
    paths = [
        "../data/result/geo"
    ]

    for file_path in paths:
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                print("Invalid path")
                print(os.path.abspath(file_path))
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
