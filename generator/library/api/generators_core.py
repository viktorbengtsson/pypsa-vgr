import numpy as np

from library.utilities import list_links, list_renewables

def create_and_store_generators(api_path, use_offwind, use_h2, use_biogas, generators, generators_t, links, links_t, biogas_efficiency, resolution):
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

        generator_path = api_path / generator
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