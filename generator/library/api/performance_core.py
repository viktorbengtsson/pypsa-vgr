import pandas as pd

from library.utilities import list_renewables

def create_and_store_sufficiency(api_path, backstop_t, market_t, loads_t, resolution):
    import_3h = (backstop_t + market_t) * resolution
    import_1d = import_3h.resample('1d').sum()
    import_1w = import_3h.resample('7D', origin='start').sum()
    import_1M = import_3h.resample('1ME').sum()

    load_3h = loads_t.squeeze() * resolution
    load_1d = load_3h.resample('1d').sum().squeeze()
    load_1w = load_3h.resample('7D', origin='start').sum().squeeze()
    load_1M = load_3h.resample('1ME').sum().squeeze()

    sufficiency_3h = (1 - import_3h/load_3h).round(4)
    sufficiency_1d = (1 - import_1d/load_1d).round(4)
    sufficiency_1w = (1 - import_1w/load_1w).round(4)
    sufficiency_1M = (1 - import_1M/load_1M).round(4)

    api_path.mkdir(parents=True, exist_ok=True)
    sufficiency_3h.to_csv(api_path / 'sufficiency_t_3h.csv.gz', compression='gzip')
    sufficiency_1d.to_csv(api_path / 'sufficiency_t_1d.csv.gz', compression='gzip')
    sufficiency_1w.to_csv(api_path / 'sufficiency_t_1w.csv.gz', compression='gzip')
    sufficiency_1M.to_csv(api_path / 'sufficiency_t_1M.csv.gz', compression='gzip')

def create_and_store_performance_metrics(api_path, use_offwind, generators, generators_t, loads_t, resolution):
    performance = pd.DataFrame(columns=['Value'])
    renewable_generators = list_renewables(use_offwind)

    performance.loc['Total energy'] = round(loads_t.sum().iloc[0] * resolution, 2)
    performance.loc['Produced energy'] = round((loads_t.sum().iloc[0] - generators_t.p['market'].sum() - generators_t.p['backstop'].sum()) * resolution, 2)
    performance.loc['Imported energy'] = round((generators_t.p['backstop'].sum() + generators_t.p['market'].sum()) * resolution, 2)
    performance.loc['Curtailed energy'] = round(((generators_t.p_max_pu[renewable_generators].sum() * generators.loc[renewable_generators]['p_nom_opt']).sum() - generators_t.p[renewable_generators].sum().sum()) * resolution, 2)
    performance.loc['Sufficiency'] = round((loads_t.sum().iloc[0] - generators_t.p['market'].sum() - generators_t.p['backstop'].sum()) / loads_t.sum().iloc[0],4)
    performance.loc['Shortfall'] = round((generators_t.p['market'].sum() + generators_t.p['backstop'].sum()) / loads_t.sum().iloc[0],4)
    performance.loc['Curtailment (of renewables)'] = 1 - generators_t.p[renewable_generators].sum().sum()/(generators_t.p_max_pu[renewable_generators].sum() * generators.loc[renewable_generators]['p_nom_opt']).sum()
    performance.loc['Curtailment (of total)'] = performance.loc['Curtailed energy'] / performance.loc['Total energy']

    performance.to_csv(api_path / 'performance_metrics.csv.gz', compression='gzip')
