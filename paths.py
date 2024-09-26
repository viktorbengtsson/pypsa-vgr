from pathlib import Path

# Define the repo root path
root_path = Path(__file__).resolve().parent

# Paths relating to model
model_path = root_path / 'model'

# Paths relating to input
input_root = root_path / 'input'

demand_root = input_root / 'demand'
demand = demand_root / 'output_core'

weather_root = input_root / 'weather'
weather = weather_root / 'output_core'

renewables_root = input_root / 'renewables'
renewables = renewables_root / 'output_core'

geo_root = input_root / 'geo'

# Paths relating to generator
generator_path = root_path / 'generator'

# Paths relating to API
api_path = root_path / 'api'

# Paths relating to dashboard
dashboard_path = root_path / 'dashboard'
