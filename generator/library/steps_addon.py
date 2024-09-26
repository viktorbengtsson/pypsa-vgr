import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths

from library.api.addon_landuse import select_and_store_land_use

# Write addon API files
def create_and_store_addon_results(config):
    data_path = paths.api_path / config['scenario']['data-path']
    data_path.mkdir(parents=True, exist_ok=True)

    if (paths.api_path / 'config.json').is_file():
        print("Results files already exist, continue")
        return

    geo = config["scenario"]["geography"]

## Select and store land use data (Specific to VGR application)
    select_and_store_land_use(paths.input_root / 'geo', 'markanvandning.csv.gz', data_path, geo)
