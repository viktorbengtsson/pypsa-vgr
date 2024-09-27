import pandas as pd
import numpy as np

from library.utilities import list_links, list_renewables

def create_and_store_lcoe(api_path, use_offwind, use_h2, use_biogas, generators, generators_t, links, links_t, stores, resolution):
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

    api_path.mkdir(parents=True, exist_ok=True)
    lcoe.to_csv(api_path / 'lcoe.csv.gz', compression='gzip')