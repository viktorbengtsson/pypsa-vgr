import pandas as pd
import numpy as np

def list_links(use_h2, use_biogas):
    links_charge = ['battery-charge']
    links_discharge = ['battery-discharge']
    if use_h2:
        links_charge += ['h2-electrolysis']
    if use_h2 or use_biogas:
        links_discharge += ['gas-turbine']

    return links_charge, links_discharge

def list_renewables(use_offwind):
    if use_offwind:
        return ['solar', 'onwind', 'offwind']
    else:
        return ['solar', 'onwind']


def create_and_store_demand(source_path, output_path, resolution):
    demand_t_3h = pd.read_csv(source_path, index_col=0, parse_dates=True) * resolution
    demand_t_1d = demand_t_3h.resample('1d').sum()
    demand_t_1w = demand_t_3h.resample('1W').sum()
    demand_t_1M = demand_t_3h.resample('1ME').sum()

    output_path.mkdir(parents=True, exist_ok=True)
    demand_t_3h.to_csv(output_path / 'demand_t_3h.csv')
    demand_t_1d.to_csv(output_path / 'demand_t_1d.csv')
    demand_t_1w.to_csv(output_path / 'demand_t_1w.csv')
    demand_t_1M.to_csv(output_path / 'demand_t_1M.csv')

def create_and_store_links(output_path, use_h2, use_biogas, links, links_t, resolution):
    links_charge, links_discharge = list_links(use_h2, use_biogas)
    links = links.loc[links_charge + links_discharge][['p_nom_opt', 'p_nom_mod', 'capital_cost', 'marginal_cost']].copy()
    links['mod_units'] = links['p_nom_opt']/links['p_nom_mod']

    links_power_t_3h = -links_t.p0[links_charge].round(9) * resolution
    links_power_t_3h[links_discharge] = -links_t.p1[links_discharge] * resolution
    links_power_t_1d = links_power_t_3h.resample('1d').sum()
    links_power_t_1w = links_power_t_3h.resample('1W').sum()
    links_power_t_1M = links_power_t_3h.resample('1ME').sum()

    for link in links_charge+links_discharge:
        link_path = output_path / link
        link_path.mkdir(parents=True, exist_ok=True)
        links.loc[link].to_csv(link_path / 'details.csv')
        links_power_t_3h[link].to_csv(link_path / 'power_t_3h.csv')
        links_power_t_1d[link].to_csv(link_path / 'power_t_1d.csv')
        links_power_t_1w[link].to_csv(link_path / 'power_t_1w.csv')
        links_power_t_1M[link].to_csv(link_path / 'power_t_1M.csv')

def create_and_store_generators(output_path, use_offwind, use_h2, use_biogas, generators, generators_t, links_t, resolution):
    links_charge, links_discharge = list_links(use_h2, use_biogas)
    generators = generators[['p_nom_mod', 'p_nom_opt', 'capital_cost', 'marginal_cost']].copy()
    generators['mod_units'] = generators['p_nom_opt']/generators['p_nom_mod']
    generators['total_energy'] = generators_t.p.sum().round(9) * resolution

    renewable_generators = list_renewables(use_offwind)

    generators_power_t_3h = generators_t.p.round(9) * resolution
    generators_power_t_1d = generators_power_t_3h.resample('1d').sum()
    generators_power_t_1w = generators_power_t_3h.resample('1W').sum()
    generators_power_t_1M = generators_power_t_3h.resample('1ME').sum()

    generators_power_to_load_t_3h = (generators_t.p[renewable_generators] - generators_t.p[renewable_generators].div(
    generators_t.p[renewable_generators].sum(axis=1), axis=0).mul(
        links_t.p0[links_charge].sum(axis=1), axis=0)).round(9) * resolution
    generators_power_to_load_t_1d = generators_power_to_load_t_3h.resample('1d').sum()
    generators_power_to_load_t_1w = generators_power_to_load_t_3h.resample('1W').sum()
    generators_power_to_load_t_1M = generators_power_to_load_t_3h.resample('1ME').sum()

    curtailment_power_t_3h = (generators_t.p_max_pu[renewable_generators].round(9) * generators.loc[renewable_generators]['p_nom_opt'] - generators_t.p[renewable_generators].round(9)) * resolution
    curtailment_power_t_1d = curtailment_power_t_3h.resample('1d').sum()
    curtailment_power_t_1w = curtailment_power_t_3h.resample('1W').sum()
    curtailment_power_t_1M = curtailment_power_t_3h.resample('1ME').sum()

    annual_curtailment = 1 - generators_t.p[renewable_generators].sum()/(generators_t.p_max_pu[renewable_generators].sum() * generators.loc[renewable_generators]['p_nom_opt'])
    annual_curtailment.replace([np.inf, -np.inf], 0, inplace=True)
    generators['curtailment'] = annual_curtailment

    for generator in generators.index:
        generator_path = output_path / generator
        generator_path.mkdir(parents=True, exist_ok=True)
        generators.loc[generator].to_csv(generator_path / 'details.csv')
        generators_power_t_3h[generator].to_csv(generator_path / 'power_t_3h.csv')
        generators_power_t_1d[generator].to_csv(generator_path / 'power_t_1d.csv')
        generators_power_t_1w[generator].to_csv(generator_path / 'power_t_1w.csv')
        generators_power_t_1M[generator].to_csv(generator_path / 'power_t_1M.csv')

        # Write data specific to solar, onwind, and offwind
        if generator in renewable_generators:
            generators_power_to_load_t_3h[generator].to_csv(generator_path / 'power_to_load_t_3h.csv')
            generators_power_to_load_t_1d[generator].to_csv(generator_path / 'power_to_load_t_1d.csv')
            generators_power_to_load_t_1w[generator].to_csv(generator_path / 'power_to_load_t_1w.csv')
            generators_power_to_load_t_1M[generator].to_csv(generator_path / 'power_to_load_t_1M.csv')

            curtailment_power_t_3h[generator].to_csv(generator_path / 'curtailment_t_3h.csv')
            curtailment_power_t_1d[generator].to_csv(generator_path / 'curtailment_t_1d.csv')
            curtailment_power_t_1w[generator].to_csv(generator_path / 'curtailment_t_1w.csv')
            curtailment_power_t_1M[generator].to_csv(generator_path / 'curtailment_t_1M.csv')

def create_and_store_stores(output_path, stores, stores_t, resolution):
    stores['mod_units'] = stores['e_nom_opt']/stores['e_nom_mod']

    stores_power_t_3h = stores_t.round(9) * resolution
    stores_power_t_1d = stores_power_t_3h.resample('1d').sum()
    stores_power_t_1w = stores_power_t_3h.resample('1W').sum()
    stores_power_t_1M = stores_power_t_3h.resample('1ME').sum()
    
    for store in stores.index:
        store_path = output_path / store
        store_path.mkdir(parents=True, exist_ok=True)
        stores.loc[store].to_csv(store_path / 'details.csv')
        stores_power_t_3h[store].to_csv(store_path / 'power_t_3h.csv')
        stores_power_t_1d[store].to_csv(store_path / 'power_t_1d.csv')
        stores_power_t_1w[store].to_csv(store_path / 'power_t_1w.csv')
        stores_power_t_1M[store].to_csv(store_path / 'power_t_1M.csv')

def create_and_store_sufficiency(output_path, backstop_t, loads_t, resolution):
    backstop_3h = backstop_t * resolution
    backstop_1d = backstop_3h.resample('1d').sum()
    backstop_1w = backstop_3h.resample('1W').sum()
    backstop_1M = backstop_3h.resample('1ME').sum()

    load_3h = loads_t.squeeze() * resolution
    load_1d = load_3h.resample('1d').sum().squeeze()
    load_1w = load_3h.resample('1W').sum().squeeze()
    load_1M = load_3h.resample('1ME').sum().squeeze()

    sufficiency_3h = (1 - backstop_3h/load_3h).round(4)
    sufficiency_1d = (1 - backstop_1d/load_1d).round(4)
    sufficiency_1w = (1 - backstop_1w/load_1w).round(4)
    sufficiency_1M = (1 - backstop_1M/load_1M).round(4)

    output_path.mkdir(parents=True, exist_ok=True)
    sufficiency_3h.to_csv(output_path / 'sufficiency_t_3h.csv')
    sufficiency_1d.to_csv(output_path / 'sufficiency_t_1d.csv')
    sufficiency_1w.to_csv(output_path / 'sufficiency_t_1w.csv')
    sufficiency_1M.to_csv(output_path / 'sufficiency_t_1M.csv')

def create_and_store_performance_metrics(output_path, loads_t, backstop_t, resolution):
    performance = pd.DataFrame(columns=['Value'])
    performance.loc['Total energy'] = round((loads_t.sum().iloc[0] - backstop_t.sum()) * resolution, 2)
    performance.loc['Backstop energy'] = backstop_t.sum().round(2) * resolution
    performance.loc['Sufficiency'] = round((loads_t.sum().iloc[0] - backstop_t.sum()) / loads_t.sum().iloc[0],4)
    performance.loc['Shortfall'] = round(backstop_t.sum() / loads_t.sum().iloc[0],4)

    performance.to_csv(output_path / 'performance_metrics.csv')

def create_and_store_worst(input_path, output_path):
    sufficiency_1d = pd.read_csv(input_path / 'sufficiency_t_1d.csv', parse_dates=True, index_col='snapshot')
    sufficiency_1w = pd.read_csv(input_path / 'sufficiency_t_1w.csv', parse_dates=True, index_col='snapshot')
    sufficiency_1M = pd.read_csv(input_path / 'sufficiency_t_1M.csv', parse_dates=True, index_col='snapshot')

    worst = pd.DataFrame(columns=['Time', 'Sufficiency'])
    worst.loc['1d'] = [sufficiency_1d.squeeze().nsmallest(1).index[0], sufficiency_1d.squeeze().nsmallest(1).iloc[0].round(4)]
    worst.loc['1w'] = [sufficiency_1w.squeeze().nsmallest(1).index[0], sufficiency_1w.squeeze().nsmallest(1).iloc[0].round(4)]
    worst.loc['1M'] = [sufficiency_1M.squeeze().nsmallest(1).index[0], sufficiency_1M.squeeze().nsmallest(1).iloc[0].round(4)]

    worst.to_csv(output_path / 'worst.csv')

def create_and_store_days_below(input_path, output_path):
    sufficiency_1d = pd.read_csv(input_path / 'sufficiency_t_1d.csv', parse_dates=True, index_col='snapshot')
    days_below = pd.DataFrame(columns=['Days'])
    for threshold in np.arange(0.95, 0, -0.05).round(2):
        days_below.loc[threshold] = (sufficiency_1d < threshold).sum()

    days_below.to_csv(output_path / 'days_below.csv')