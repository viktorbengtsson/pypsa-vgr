from library.utilities import list_links

def create_and_store_links(api_path, use_h2, use_biogas, links, links_t, resolution):
    links_charge, links_discharge = list_links(use_h2, use_biogas)
    links = links.loc[links_charge + links_discharge][['p_nom_opt', 'p_nom_mod', 'capital_cost', 'marginal_cost']].copy()
    links['mod_units'] = links['p_nom_opt']/links['p_nom_mod']
    
    links_power_t_3h = -links_t.p0[links_charge].round(9) * resolution
    links_power_t_3h[links_discharge] = -links_t.p1[links_discharge] * resolution
    links_power_t_1d = links_power_t_3h.resample('1d').sum()
    links_power_t_1w = links_power_t_3h.resample('7D', origin='start').sum()
    links_power_t_1M = links_power_t_3h.resample('1ME').sum()

    for link in links_charge+links_discharge:
        link_path = api_path / link
        link_path.mkdir(parents=True, exist_ok=True)
        links.loc[link].to_csv(link_path / 'details.csv.gz', compression='gzip')
        links_power_t_3h[link].to_csv(link_path / 'power_t_3h.csv.gz', compression='gzip')
        links_power_t_1d[link].to_csv(link_path / 'power_t_1d.csv.gz', compression='gzip')
        links_power_t_1w[link].to_csv(link_path / 'power_t_1w.csv.gz', compression='gzip')
        links_power_t_1M[link].to_csv(link_path / 'power_t_1M.csv.gz', compression='gzip')
