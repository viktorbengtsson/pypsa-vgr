from library.utilities import list_renewables

def create_and_store_stores(api_path, use_offwind, use_h2, stores, stores_t, links, links_t, loads_t, generators_t, gas_turbine_efficiency, resolution):
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
        store_path = api_path / store
        store_path.mkdir(parents=True, exist_ok=True)
        stores_modified.loc[store].to_csv(store_path / 'details.csv.gz', compression='gzip')
        if len(stores_power_t_3h.columns) > 0:
            stores_power_t_3h[store].to_csv(store_path / 'power_t_3h.csv.gz', compression='gzip')
            stores_power_t_1d[store].to_csv(store_path / 'power_t_1d.csv.gz', compression='gzip')
            stores_power_t_1w[store].to_csv(store_path / 'power_t_1w.csv.gz', compression='gzip')
            stores_power_t_1M[store].to_csv(store_path / 'power_t_1M.csv.gz', compression='gzip')
