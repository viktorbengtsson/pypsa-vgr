import sys
import shutil

from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths

def clear_files_not_needed_for_dashboard_for_config(config):
    data_path = paths.output_path / config['scenario']['data-path']

    paths_array = [
        data_path / 'statistics.pkl',
        data_path / 'network.nc',
    ]

    for item in paths_array:
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f'Failed to delete {item}. Reason: {e}')


def clear_files_not_needed_for_dashboard():
    geo_path = paths.output_path / 'geo'

    paths_array = [
        geo_path
    ]

    for item in paths_array:
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f'Failed to delete {item}. Reason: {e}')
