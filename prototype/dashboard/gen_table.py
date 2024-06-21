import streamlit as st
import numpy as np
import pandas as pd
from data_loading import network_data_from_variables
from visualizations import get_labels

def size_text(index):
    if index == 0:
        return "turbiner"
    elif index == 1:
        return "turbiner"
    elif index == 2:
        return "hektar"
    elif index == 3:
        return "generatorer"
    elif index == 4:
        return "ton"
    elif index == 5:
        return "elektrolysverk"
    elif index == 6:
        return "parker"
    else:
        return ""

def render_generators_table(st_obj, config):
    
    NETWORK = network_data_from_variables("../", config)
    parameters = pd.read_csv("../../data/assumptions.csv")
    parameters.set_index(['technology', 'parameter'], inplace=True)

    labels = get_labels()

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

    st_obj.dataframe(data, column_config={
        "Totalkostnad": st.column_config.ProgressColumn(
            "Totalkostnad",
            help="Total kostnad med procent-andel av total",
            format="%f MSEK",
            min_value=0,
            max_value=sum_total_cost,
        )
    })
