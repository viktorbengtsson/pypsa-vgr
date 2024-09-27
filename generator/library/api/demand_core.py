import pandas as pd

def create_and_store_demand(source_path, api_path, resolution):
    demand_t_3h = pd.read_csv(source_path, compression='gzip', index_col=0, parse_dates=True) * resolution
    demand_t_1d = demand_t_3h.resample('1d').sum()
    demand_t_1w = demand_t_3h.resample('7D', origin='start').sum()
    demand_t_1M = demand_t_3h.resample('1ME').sum()

    api_path.mkdir(parents=True, exist_ok=True)
    demand_t_3h.to_csv(api_path / 'demand_t_3h.csv.gz', compression='gzip')
    demand_t_1d.to_csv(api_path / 'demand_t_1d.csv.gz', compression='gzip')
    demand_t_1w.to_csv(api_path / 'demand_t_1w.csv.gz', compression='gzip')
    demand_t_1M.to_csv(api_path / 'demand_t_1M.csv.gz', compression='gzip')
