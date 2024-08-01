import pandas as pd
import numpy as np

def _get_labels():
    return {
        "Backstop" : "Backstop",
        "Biogas market" : "Biogas",
        "Offwind park" : "Vindkraft (hav)",
        "Onwind park" : "Vindkraft (land)",
        "Solar park" : "Sol",
        "H2 storage": "Vätgas",
        "Battery storage": "Batteri",
        "Gas turbine": "Gas turbin",
        "H2 electrolysis": "Vätgas electrolys",
        "Battery charge": "Batteri laddning",
        "Biogas input": "Biogas",
        "SMR nuclear": "Kärnkraft",
        "Conventional nuclear": "Kärnkraft",
        "Combined Cycle Gas turbine": "Kombinerad gas turbin",
        "Simple Cycle Gas turbine": "Enkel gas turbin",
        "Total": "Total",
    }
def _get_plot_config(columns):
    labels = _get_labels()
    labels_length = len(labels)

    main_series_labels = []
    main_series_keys = []
    for col in columns:
        if col != "Backstop":
            main_series_labels.append(labels[col])
            main_series_keys.append(col)

    return [
        main_series_labels,
        main_series_keys,
    ]

def _capacity(NETWORK):
    return NETWORK.generators_t.p.abs()

def _capacity_monthly(NETWORK, parameters):
    capacity_monthly = NETWORK.generators_t.p.resample('ME').sum()*3 / 1_000
    capacity_monthly['Biogas input'] = capacity_monthly['Biogas input'] * float(parameters.loc['biogas', 'efficiency'].value)
    return capacity_monthly

def _table(NETWORK, parameters):
    labels = _get_labels()

    column_names = {
        'total_cost': 'Totalkostnad',
        'annual_cost': 'Årskostnad',
        'lifetime': 'Livslängd',
        'p_nom_opt': 'Kapacitet',
        'generators': 'Kraftverk',
        'energy_produced': 'Producerad energi',
    }

    generator_index = NETWORK.generators.index.difference(['Backstop', 'Biogas input'])

    generators = pd.concat([
        NETWORK.generators.loc[NETWORK.generators.index.isin(generator_index)][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']],
        NETWORK.links.loc[['Combined Cycle Gas turbine', 'Simple Cycle Gas turbine']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']]
    ])

    generators['annual_cost'] = np.where(generators['p_nom_opt'] != 0, generators['capital_cost'] * generators['p_nom_opt'], 0)
    generators['energy_produced'] = NETWORK.generators_t.p.loc[:, generator_index].sum() * 3
    generators['generators'] = generators['p_nom_opt'] / generators['p_nom_mod']

    other = NETWORK.links.loc[['H2 electrolysis', 'Battery charge']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']]
    other['annual_cost'] = np.where(other['p_nom_opt'] != 0, other['capital_cost'] * other['p_nom_opt'], 0)

    stores = NETWORK.stores.loc[["H2 storage", "Battery storage"]][['capital_cost', 'marginal_cost', 'lifetime', 'e_nom_opt']]
    stores['annual_cost'] = np.where(stores['e_nom_opt'] != 0, stores['capital_cost'] * stores['e_nom_opt'], 0)
    stores.rename(columns={'e_nom_opt': 'p_nom_opt'}, inplace=True)

    biogas = NETWORK.generators.loc[['Biogas input']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']]
    biogas['energy_produced'] = NETWORK.generators_t.p[['Biogas input']].sum() * 3 * float(parameters.loc['biogas', 'efficiency'].value)
    biogas['annual_cost'] = np.where(biogas['p_nom_opt'] != 0, biogas['marginal_cost'] * biogas['energy_produced'] / float(parameters.loc['biogas', 'efficiency'].value), 0)
    biogas[['lifetime', 'p_nom_opt', 'total_cost']] = 0

    system = pd.concat([generators, other, stores, biogas]).drop(columns=['capital_cost', 'marginal_cost'])[['p_nom_opt', 'generators', 'lifetime', 'energy_produced', 'annual_cost']]

    totals = pd.DataFrame(columns=system.columns, index=['Total'])
    totals['energy_produced'] = system['energy_produced'].sum()
    totals['annual_cost'] = system['annual_cost'].sum()

    system = pd.concat([system, totals]).rename(columns=column_names)

    years = lambda s: f'{s:,.0f} år'.replace(',', ' ')
    million_cost = lambda s: f'{s/1_000_000:,.0f} MSEK'.replace(',', ' ')
    energy = lambda s: f'{s/1_000:,.0f} GWh'.replace(',', ' ')
    price = lambda s: f'{s:,.0f} SEK'.replace(',', ' ')
    system.abs().style.format({'Livslängd': years, 'Producerad energi': energy, 'Pris': price, 'Årskostnad': million_cost, 'Totalkostnad': million_cost}, precision=0, na_rep='-')
    
    data = system
    data.index = [labels[col] for col in data.index]
    data = data.fillna("-")

    sum_total_cost = int(totals["annual_cost"].sum())

    return {
        "data": data,
        "sum_total_cost": sum_total_cost
    }

def _energy_compare(NETWORK, parameters):
    generator_index = NETWORK.generators.index.difference(['Backstop', 'Biogas input'])

    GEN = pd.concat([
        NETWORK.generators.loc[NETWORK.generators.index.isin(generator_index)][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']],
        NETWORK.links.loc[['Combined Cycle Gas turbine', 'Simple Cycle Gas turbine']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']]
    ])
    GEN['annual_cost'] = np.where(GEN['p_nom_opt'] != 0, GEN['capital_cost'] * GEN['p_nom_opt'], 0)
    GEN = GEN["annual_cost"]

    STOR = NETWORK.stores.loc[["H2 storage", "Battery storage"]][['capital_cost', 'marginal_cost', 'lifetime', 'e_nom_opt']]
    STOR['annual_cost'] = np.where(STOR['e_nom_opt'] != 0, STOR['capital_cost'] * STOR['e_nom_opt'], 0)
    STOR = STOR["annual_cost"]

    gen_columns = [col for idx, col in enumerate(GEN.index) if GEN.iloc[idx].sum() > 0]
    [
        gen_main_series_labels,
        gen_main_series_keys,
    ] = _get_plot_config(gen_columns)

    GEN = GEN[[col for col in gen_columns if col in gen_main_series_keys]] / 1_000_000
    GEN.index = [col for col in gen_main_series_labels]

    stor_columns = [col for idx, col in enumerate(STOR.index) if STOR.iloc[idx].sum() > 0]
    [
        stor_main_series_labels,
        stor_main_series_keys,
    ] = _get_plot_config(stor_columns)

    STOR = STOR[[col for col in stor_columns if col in stor_main_series_keys]] / 1_000_000
    STOR.index = [col for col in stor_main_series_labels]

    GEN_DATA = pd.DataFrame({'Category': ["Produktion (MSEK)"] * len(GEN.index), 'Type':GEN.index, 'Value':GEN.values })
    STOR_DATA = pd.DataFrame({'Category': ["Lagring (MSEK)"] * len(STOR.index),  'Type':STOR.index, 'Value':STOR.values })

    return {
        "data": pd.concat([GEN_DATA, STOR_DATA]),
        "main_series_labels": gen_main_series_labels + stor_main_series_labels,
        "main_series_keys": gen_main_series_keys + stor_main_series_keys
    }

def _widgets(NETWORK, STATISTICS, parameters):
    if NETWORK.generators["p_nom_opt"].sum() == 0:
        return None

    generator_index = NETWORK.generators.index.difference(['Backstop', 'Biogas input'])

    generators = pd.concat([
        NETWORK.generators.loc[NETWORK.generators.index.isin(generator_index)][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']],
        NETWORK.links.loc[['Combined Cycle Gas turbine', 'Simple Cycle Gas turbine']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']]
    ])

    generators['annual_cost'] = np.where(generators['p_nom_opt'] != 0, generators['capital_cost'] * generators['p_nom_opt'], 0)
    generators['energy_produced'] = NETWORK.generators_t.p.loc[:, generator_index].sum() * 3
    generators['generators'] = generators['p_nom_opt'] / generators['p_nom_mod']

    stores = NETWORK.stores.loc[["H2 storage", "Battery storage"]][['capital_cost', 'marginal_cost', 'lifetime', 'e_nom_opt']]
    stores['annual_cost'] = np.where(stores['e_nom_opt'] != 0, stores['capital_cost'] * stores['e_nom_opt'], 0)
    stores.rename(columns={'e_nom_opt': 'p_nom_opt'}, inplace=True)

    backstop_total = NETWORK.generators_t.p.loc[:, 'Backstop'].sum()*3 / 1_000_000
    #backstop_fraction = backstop_total / (NETWORK.loads_t.p['Desired load'].sum() * 3 / 1_000_000)
    backstop_fraction = NETWORK.generators_t.p[['Backstop']].sum().sum() / NETWORK.loads_t.p.sum().sum()

    curtailment_total = STATISTICS[['Curtailment']].sum() / 1_000_000
    curtailment_fraction = STATISTICS[['Curtailment']].sum() / (STATISTICS[['Curtailment']].sum() + NETWORK.generators_t.p[['Offwind park', 'Onwind park', 'Solar park', 'Conventional nuclear', 'SMR nuclear', 'Biogas input']].sum().sum()*3)
    curtailment_total = curtailment_total['Curtailment']
    curtailment_fraction = curtailment_fraction['Curtailment']

    biogas = NETWORK.generators.loc[['Biogas input']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']]
    biogas['energy_produced'] = NETWORK.generators_t.p[['Biogas input']].sum() * 3 * float(parameters.loc['biogas', 'efficiency'].value)
    biogas['annual_cost'] = np.where(biogas['p_nom_opt'] != 0, biogas['marginal_cost'] * biogas['energy_produced'] / float(parameters.loc['biogas', 'efficiency'].value), 0)
    #biogas_key = ["Combined Cycle Gas turbine", "Simple Cycle Gas turbine"]
    biogas_price = biogas['annual_cost'].sum() / biogas['energy_produced'].sum() / 1000 if biogas['energy_produced'].sum() > 0 else 0
      
    return [generators, stores, biogas_price, backstop_total, backstop_fraction, curtailment_total, curtailment_fraction]
    

def collect_data(network, statistics, assumptions):

    return {
        "capacity": _capacity(network),
        "capacity_monthly": _capacity_monthly(network, assumptions),
        "table": _table(network, assumptions),
        "energy_compare": _energy_compare(network, assumptions),
        "widgets": _widgets(network, statistics, assumptions),
    }
