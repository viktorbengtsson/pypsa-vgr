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
    demand_t_3h = pd.read_csv(source_path, compression='gzip', index_col=0, parse_dates=True) * resolution
    demand_t_1d = demand_t_3h.resample('1d').sum()
    demand_t_1w = demand_t_3h.resample('7D', origin='start').sum()
    demand_t_1M = demand_t_3h.resample('1ME').sum()

    output_path.mkdir(parents=True, exist_ok=True)
    demand_t_3h.to_csv(output_path / 'demand_t_3h.csv.gz', compression='gzip')
    demand_t_1d.to_csv(output_path / 'demand_t_1d.csv.gz', compression='gzip')
    demand_t_1w.to_csv(output_path / 'demand_t_1w.csv.gz', compression='gzip')
    demand_t_1M.to_csv(output_path / 'demand_t_1M.csv.gz', compression='gzip')

def create_and_store_links(output_path, use_h2, use_biogas, links, links_t, resolution):
    links_charge, links_discharge = list_links(use_h2, use_biogas)
    links = links.loc[links_charge + links_discharge][['p_nom_opt', 'p_nom_mod', 'capital_cost', 'marginal_cost']].copy()
    links['mod_units'] = links['p_nom_opt']/links['p_nom_mod']
    
    links_power_t_3h = -links_t.p0[links_charge].round(9) * resolution
    links_power_t_3h[links_discharge] = -links_t.p1[links_discharge] * resolution
    links_power_t_1d = links_power_t_3h.resample('1d').sum()
    links_power_t_1w = links_power_t_3h.resample('7D', origin='start').sum()
    links_power_t_1M = links_power_t_3h.resample('1ME').sum()

    for link in links_charge+links_discharge:
        link_path = output_path / link
        link_path.mkdir(parents=True, exist_ok=True)
        links.loc[link].to_csv(link_path / 'details.csv.gz', compression='gzip')
        links_power_t_3h[link].to_csv(link_path / 'power_t_3h.csv.gz', compression='gzip')
        links_power_t_1d[link].to_csv(link_path / 'power_t_1d.csv.gz', compression='gzip')
        links_power_t_1w[link].to_csv(link_path / 'power_t_1w.csv.gz', compression='gzip')
        links_power_t_1M[link].to_csv(link_path / 'power_t_1M.csv.gz', compression='gzip')

def create_and_store_generators(output_path, use_offwind, use_h2, use_biogas, generators, generators_t, links, links_t, biogas_efficiency, resolution):
    links_charge, links_discharge = list_links(use_h2, use_biogas)
    renewable_generators = list_renewables(use_offwind)

    # Load generators table (add gas turbine if it exists)
    generators = generators[['p_nom_mod', 'p_nom_opt', 'capital_cost', 'marginal_cost']].copy()
    if use_h2 or use_biogas:
        generators.loc['biogas-turbine'] = links.loc['gas-turbine'][['p_nom_mod', 'p_nom_opt', 'capital_cost', 'marginal_cost']]

    # Add number of units
    generators['mod_units'] = generators['p_nom_opt']/generators['p_nom_mod']
    generators.loc['biogas-turbine', 'mod_units'] = 0 # Currently we do not consider a typical size of gas turbine, just a minimal nominal power

    # Calculate 
    generators['total_energy'] = generators_t.p.sum().round(9) * resolution
    if use_biogas:
        generators.loc['biogas-turbine', 'total_energy'] = generators.loc['biogas-market', 'total_energy'] * biogas_efficiency # Convert thermal energy of biogas to electrical energy
        generators['fraction_energy'] = generators['total_energy'] / (generators_t.p[renewable_generators].sum().sum()*resolution + generators_t.p[['biogas-market']].sum().sum()*biogas_efficiency*resolution) # Divisor is total energy produced in system
    else:
        generators['fraction_energy'] = generators['total_energy'] / (generators_t.p[renewable_generators].sum().sum()*resolution)

    # Calculate power 
    generators_power_t_3h = generators_t.p.round(9) * resolution
    if use_biogas:
        generators_power_t_3h['biogas-turbine'] = generators_power_t_3h['biogas-market'] * biogas_efficiency
    generators_power_t_1d = generators_power_t_3h.resample('1d').sum()
    generators_power_t_1w = generators_power_t_3h.resample('7D', origin='start').sum()
    generators_power_t_1M = generators_power_t_3h.resample('1ME').sum()

    # Calculate power to load for renewable generators
    generators_power_to_load_t_3h = (generators_t.p[renewable_generators] - generators_t.p[renewable_generators].div(
    generators_t.p[renewable_generators].sum(axis=1), axis=0).mul(
        links_t.p0[links_charge].sum(axis=1), axis=0)).round(9) * resolution
    generators_power_to_load_t_1d = generators_power_to_load_t_3h.resample('1d').sum()
    generators_power_to_load_t_1w = generators_power_to_load_t_3h.resample('7D', origin='start').sum()
    generators_power_to_load_t_1M = generators_power_to_load_t_3h.resample('1ME').sum()

    # Calculate curtailment timeseries and resample
    curtailment_power_t_3h = (generators_t.p_max_pu[renewable_generators].round(9) * generators.loc[renewable_generators]['p_nom_opt'] - generators_t.p[renewable_generators].round(9)) * resolution
    curtailment_power_t_1d = curtailment_power_t_3h.resample('1d').sum()
    curtailment_power_t_1w = curtailment_power_t_3h.resample('7D', origin='start').sum()
    curtailment_power_t_1M = curtailment_power_t_3h.resample('1ME').sum()

    # Add total/annual curtailment to generators df
    annual_curtailment = 1 - generators_t.p[renewable_generators].sum()/(generators_t.p_max_pu[renewable_generators].sum() * generators.loc[renewable_generators,'p_nom_opt'])
    if use_biogas:
        annual_curtailment['biogas-turbine'] = 1 - generators_power_t_3h['biogas-turbine'].sum()/(365*24/3 * generators.loc['biogas-turbine','p_nom_opt'])
    annual_curtailment.replace([np.inf, -np.inf], 0, inplace=True)
    generators['curtailment'] = annual_curtailment

    for generator in generators.index:
        if not use_biogas and generator == 'biogas-turbine':
            continue

        generator_path = output_path / generator
        generator_path.mkdir(parents=True, exist_ok=True)
        generators.loc[generator].to_csv(generator_path / 'details.csv.gz', compression='gzip')
        generators_power_t_3h[generator].to_csv(generator_path / 'power_t_3h.csv.gz', compression='gzip')
        generators_power_t_1d[generator].to_csv(generator_path / 'power_t_1d.csv.gz', compression='gzip')
        generators_power_t_1w[generator].to_csv(generator_path / 'power_t_1w.csv.gz', compression='gzip')
        generators_power_t_1M[generator].to_csv(generator_path / 'power_t_1M.csv.gz', compression='gzip')

        # Write data specific to solar, onwind, and offwind
        if generator in renewable_generators:
            generators_power_to_load_t_3h[generator].to_csv(generator_path / 'power_to_load_t_3h.csv.gz', compression='gzip')
            generators_power_to_load_t_1d[generator].to_csv(generator_path / 'power_to_load_t_1d.csv.gz', compression='gzip')
            generators_power_to_load_t_1w[generator].to_csv(generator_path / 'power_to_load_t_1w.csv.gz', compression='gzip')
            generators_power_to_load_t_1M[generator].to_csv(generator_path / 'power_to_load_t_1M.csv.gz', compression='gzip')

            curtailment_power_t_3h[generator].to_csv(generator_path / 'curtailment_t_3h.csv.gz', compression='gzip')
            curtailment_power_t_1d[generator].to_csv(generator_path / 'curtailment_t_1d.csv.gz', compression='gzip')
            curtailment_power_t_1w[generator].to_csv(generator_path / 'curtailment_t_1w.csv.gz', compression='gzip')
            curtailment_power_t_1M[generator].to_csv(generator_path / 'curtailment_t_1M.csv.gz', compression='gzip')

def create_and_store_stores(output_path, use_offwind, use_h2, stores, stores_t, links, links_t, loads_t, generators_t, gas_turbine_efficiency, resolution):
    renewable_generators = list_renewables(use_offwind)

    stores_modified = stores[['e_nom_mod', 'e_nom_opt', 'capital_cost', 'marginal_cost']].copy()
    stores_modified['mod_units'] = stores_modified['e_nom_opt']/stores_modified['e_nom_mod']

    stores_modified.loc['battery', 'p_nom_opt_charge'] = links.loc['battery-charge', 'p_nom_opt']
    stores_modified.loc['battery', 'p_nom_opt_discharge'] = links.loc['battery-discharge', 'p_nom_opt']
    stores_modified.loc['battery', 'fraction_energy_in'] = links_t.p0['battery-charge'].sum()/generators_t.p[renewable_generators].sum().sum()
    stores_modified.loc['battery', 'fraction_energy_out'] = -links_t.p1['battery-discharge'].sum() / (loads_t.p.sum().iloc[0] - generators_t.p['backstop'].sum())

    if use_h2 and stores_modified.loc['h2', 'e_nom_opt'] > 0:
        stores_modified.loc['h2', 'p_nom_opt_charge'] = links.loc['h2-electrolysis', 'p_nom_opt']
        stores_modified.loc['h2', 'p_nom_opt_discharge'] = links.loc['gas-turbine', 'p_nom_opt']
        stores.loc['h2', 'fraction_energy_in'] = links_t.p0['h2-electrolysis'].sum()/generators_t.p[renewable_generators].sum().sum()
        stores_modified.loc['h2', 'fraction_energy_out'] = -links_t.p1['H2 pipeline'].round(9).sum() * gas_turbine_efficiency / (loads_t.p.sum().iloc[0] - generators_t.p['backstop'].sum())

    stores_power_t_3h = stores_t.round(9) * resolution
    stores_power_t_1d = stores_power_t_3h.resample('1d').sum()
    stores_power_t_1w = stores_power_t_3h.resample('7D', origin='start').sum()
    stores_power_t_1M = stores_power_t_3h.resample('1ME').sum()
    
    for store in stores_modified.index:
        store_path = output_path / store
        store_path.mkdir(parents=True, exist_ok=True)
        stores_modified.loc[store].to_csv(store_path / 'details.csv.gz', compression='gzip')
        if len(stores_power_t_3h.columns) > 0:
            stores_power_t_3h[store].to_csv(store_path / 'power_t_3h.csv.gz', compression='gzip')
            stores_power_t_1d[store].to_csv(store_path / 'power_t_1d.csv.gz', compression='gzip')
            stores_power_t_1w[store].to_csv(store_path / 'power_t_1w.csv.gz', compression='gzip')
            stores_power_t_1M[store].to_csv(store_path / 'power_t_1M.csv.gz', compression='gzip')

def create_and_store_sufficiency(output_path, backstop_t, market_t, loads_t, resolution):
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

    output_path.mkdir(parents=True, exist_ok=True)
    sufficiency_3h.to_csv(output_path / 'sufficiency_t_3h.csv.gz', compression='gzip')
    sufficiency_1d.to_csv(output_path / 'sufficiency_t_1d.csv.gz', compression='gzip')
    sufficiency_1w.to_csv(output_path / 'sufficiency_t_1w.csv.gz', compression='gzip')
    sufficiency_1M.to_csv(output_path / 'sufficiency_t_1M.csv.gz', compression='gzip')

def create_and_store_performance_metrics(output_path, use_offwind, generators, generators_t, loads_t, resolution):
    performance = pd.DataFrame(columns=['Value'])
    renewable_generators = list_renewables(use_offwind)

    performance.loc['Total energy'] = round(loads_t.sum().iloc[0] * resolution, 2)
    performance.loc['Produced energy'] = round((loads_t.sum().iloc[0] - generators_t.p['market'].sum() - generators_t.p['backstop'].sum()) * resolution, 2)
    performance.loc['Imported energy'] = round((generators_t.p['backstop'].sum() + generators_t.p['market'].sum()) * resolution, 2)
    performance.loc['Curtailed energy'] = (generators_t.p_max_pu[renewable_generators].sum() * generators.loc[renewable_generators]['p_nom_opt']).sum() - generators_t.p[renewable_generators].sum().sum()
    performance.loc['Sufficiency'] = round((loads_t.sum().iloc[0] - generators_t.p['market'].sum() - generators_t.p['backstop'].sum()) / loads_t.sum().iloc[0],4)
    performance.loc['Shortfall'] = round((generators_t.p['market'].sum() + generators_t.p['backstop'].sum()) / loads_t.sum().iloc[0],4)
    performance.loc['Curtailment (of renewables)'] = 1 - generators_t.p[renewable_generators].sum().sum()/(generators_t.p_max_pu[renewable_generators].sum() * generators.loc[renewable_generators]['p_nom_opt']).sum()
    performance.loc['Curtailment (of total)'] = performance.loc['Curtailed energy'] / performance.loc['Total energy']

    performance.to_csv(output_path / 'performance_metrics.csv.gz', compression='gzip')

def create_and_store_lcoe(output_path, use_offwind, use_h2, use_biogas, generators, generators_t, links, links_t, stores, resolution):
    # Calculate renewables distribution and cost distribution (helper for the LCOE further down)
    energy = pd.DataFrame(columns=['energy_to_load', 'cost_to_load', 'energy_to_battery', 'cost_to_battery', 'energy_to_h2', 'cost_to_h2', 'total_energy', 'total_cost'])
    renewable_generators = list_renewables(use_offwind)
    links_charge, links_discharge = list_links(use_h2, use_biogas)

    energy['total_energy'] = generators_t[renewable_generators].sum() * resolution
    energy['total_cost'] = generators.loc[renewable_generators]['p_nom_opt']*generators.loc[renewable_generators]['capital_cost'] + energy['total_energy'] * generators.loc[renewable_generators]['marginal_cost']

    energy['energy_to_load'] = (generators_t[renewable_generators] - generators_t[renewable_generators].div(
    generators_t[renewable_generators].sum(axis=1), axis=0).mul(
        links_t.p0[links_charge].sum(axis=1), axis=0)).sum() * 3
    energy['cost_to_load'] = energy['energy_to_load'] / energy['total_energy'] * energy['total_cost']

    energy['energy_to_battery'] = generators_t[renewable_generators].div(generators_t[renewable_generators].sum(axis=1), axis=0).mul(links_t.p0['battery-charge'], axis=0).sum() * resolution
    energy['cost_to_battery'] = energy['energy_to_battery'] / energy['total_energy'] * energy['total_cost']

    if use_h2:
        energy['energy_to_h2'] = generators_t[renewable_generators].div(generators_t[renewable_generators].sum(axis=1), axis=0).mul(links_t.p0['h2-electrolysis'], axis=0).sum() * resolution
        energy['cost_to_h2'] = energy['energy_to_h2'] / energy['total_energy'] * energy['total_cost']

    # Define the LCOE data frame
    lcoe = pd.DataFrame(columns=['total_energy', 'total_cost', 'lcoe', 'curtailment'], index=['solar', 'onwind', 'offwind', 'battery', 'biogas', 'h2'])

    # Add renewables to load (calculated above)
    lcoe['total_energy'] = energy['energy_to_load']
    lcoe['total_cost'] = energy['cost_to_load']

    # Battery calculations
    # Add total energy output
    lcoe.loc['battery', 'total_energy'] = -links_t.p1['battery-discharge'].sum() * resolution

    # Add electricity input cost
    lcoe.loc['battery', 'total_cost'] = energy['cost_to_battery'].sum()
    # Add inverter (modelled as links) capital costs (for now these have no marginal costs)
    lcoe.loc['battery', 'total_cost'] += (links.loc[['battery-charge', 'battery-discharge']]['capital_cost']*links.loc[['battery-charge', 'battery-discharge']]['p_nom_opt']).sum()
    # Add storage capital costs
    lcoe.loc['battery', 'total_cost'] += stores.loc['battery', 'capital_cost'] * stores.loc['battery', 'e_nom_opt']

    #H2 calculations

    h2_gas_fraction = 0
    if use_h2:
        if use_biogas:
            h2_gas_fraction = links_t.p0['H2 pipeline'].sum() / (generators_t[['biogas-market']].sum().values[0] + links_t.p0['H2 pipeline'].sum())
        else:
            h2_gas_fraction = 1

        # Add total energy output
        lcoe.loc['h2', 'total_energy'] = -links_t.p1['gas-turbine'].sum() * resolution * h2_gas_fraction

        # Add electricity input cost
        lcoe.loc['h2', 'total_cost'] = energy['cost_to_h2'].sum()
        # Add electrolysis (modelled as link) capital cost (for now this has no marginal costs)
        lcoe.loc['h2', 'total_cost'] += links.loc['h2-electrolysis', 'capital_cost'] * links.loc['h2-electrolysis','p_nom_opt']
        # Add storage capical cost (for not there is not marginal cost)
        lcoe.loc['h2', 'total_cost'] += stores.loc['h2', 'capital_cost'] * stores.loc['h2','e_nom_opt']
        # Add gas turbine (modelled as link) fractional capital cost (fraction of h2 in total gas)
        lcoe.loc['h2', 'total_cost'] += links.loc['gas-turbine', 'capital_cost'] * links.loc['gas-turbine','p_nom_opt'] * h2_gas_fraction
        # Add gas turbine (modelled as link) marginal cost
        lcoe.loc['h2', 'total_cost'] += links.loc['gas-turbine', 'marginal_cost'] * lcoe.loc['h2', 'total_energy']

    # Biogas calculations

    if use_biogas:
        # Add total energy output
        lcoe.loc['biogas', 'total_energy'] = -links_t.p1['gas-turbine'].sum() * resolution * (1 - h2_gas_fraction)

        # Add biogas input cost
        lcoe.loc['biogas', 'total_cost'] = generators_t[['biogas-market']].sum().iloc[0] * generators.loc['biogas-market', 'marginal_cost'] * resolution
        # Add gas turbine (modelled as link) fractional capital cost (fraction of h2 in total gas)
        lcoe.loc['biogas', 'total_cost'] += links.loc['gas-turbine', 'capital_cost'] * links.loc['gas-turbine','p_nom_opt'] * (1 - h2_gas_fraction)
        # Add gas turbine (modelled as link) marginal cost
        lcoe.loc['biogas', 'total_cost'] += links.loc['gas-turbine', 'marginal_cost'] * lcoe.loc['biogas', 'total_energy']

    # Calculate LCOE per energy type
    lcoe = lcoe.round(9)
    lcoe['lcoe'] = (lcoe['total_cost']/lcoe['total_energy']) / 1_000
    lcoe['lcoe'] = lcoe['lcoe'].replace([np.inf, -np.inf], np.nan)

    output_path.mkdir(parents=True, exist_ok=True)
    lcoe.to_csv(output_path / 'lcoe.csv.gz', compression='gzip')

def select_and_store_land_use(land_path, land_file, data_path, geo):
    land_use = pd.read_csv(land_path / land_file, compression='gzip', index_col='Kod')
    land_use.loc[geo.split(':')[-1]].to_csv(data_path / 'landuse.csv.gz', compression='gzip')