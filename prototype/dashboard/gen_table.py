import streamlit as st
import numpy as np
import pandas as pd
from data_loading import essential_data_from_variables
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
    [
        ASSUMPTIONS,
        DEMAND,
        NETWORK,
        STATISTICS
    ] = essential_data_from_variables("../", config)
    parameters = pd.read_csv("../../data/assumptions.csv")
    parameters.set_index(['technology', 'parameter'], inplace=True)

    labels = get_labels()

    generator_column_names = {
        'total_cost': 'Totalkostnad',
        'annual_cost': 'Årskostnad',
        'lifetime': 'Livslängd',
        'p_nom_opt': 'Kapacitet',
        'energy_produced': 'Producerad energi',
        'shadow_price': 'Skuggpris'
    }

    store_column_names = {
        'total_cost': 'Totalkostnad',
        'annual_cost': 'Årskostnad',
        'lifetime': 'Livslängd',
        'e_nom_opt': 'Kapacitet'
    }

    generators = pd.concat([
        NETWORK.generators.loc[['Solar park', 'Onwind park', 'Offwind park']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']],
        NETWORK.links.loc[['Gas turbine']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']]
    ])

    generators['total_cost'] = np.where(generators['p_nom_opt'] != 0, generators['capital_cost'] * generators['p_nom_opt'], 0)
    generators['annual_cost'] = np.where(generators['p_nom_opt'] != 0, generators['total_cost'] / generators['lifetime'], 0)
    generators['energy_produced'] = NETWORK.generators_t.p[['Solar park', 'Onwind park', 'Offwind park']].sum() * 3
    generators.loc['Gas turbine', 'energy_produced'] = 0
    generators['shadow_price'] = np.where(generators['energy_produced'] != 0, generators['annual_cost'] / generators['energy_produced'], 0)
    generators.drop(columns=['capital_cost', 'marginal_cost'], inplace=True)

    generators['total_cost'] = generators['total_cost'].apply(lambda x: int(f"{int(x/1_000_000):,}".replace(',', '')))
    generators['annual_cost'] = generators['annual_cost'].apply(lambda x: f"{int(x/1_000_000):,}".replace(',', ' ') + " MSEK/year")
    generators['energy_produced'] = generators['energy_produced'].apply(lambda x: f"{int(x/1_000):,}".replace(',', ' ') + " GWh/year")
    generators['shadow_price'] = generators['shadow_price'].apply(lambda x: f"{int(x):,}".replace(',', ' ') + " SEK/MWh")
    generators['lifetime'] = generators['lifetime'].apply(lambda x: f"{int(x)} years")
    generators['p_nom_opt'] = generators['p_nom_opt'].apply(lambda x: f"{int(x):,}".replace(',', ' ') + " MW")
    generators = generators[['p_nom_opt', 'lifetime', 'energy_produced', 'annual_cost', 'shadow_price', 'total_cost']]
    generators.rename(columns=generator_column_names, inplace=True)

    biogas = NETWORK.generators.loc[['Biogas market']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']]
    biogas['energy_produced'] = NETWORK.generators_t.p[['Biogas market']].sum() * 3 * float(parameters.loc['biogas', 'efficiency'].value)
    biogas['annual_cost'] = np.where(biogas['p_nom_opt'] != 0, biogas['marginal_cost'] * biogas['energy_produced'] / float(parameters.loc['biogas', 'efficiency'].value), 0)
    biogas['shadow_price'] = np.where(biogas['p_nom_opt'] != 0, biogas['annual_cost'] / biogas['energy_produced'], 0)
    biogas['lifetime'] = 0
    biogas['p_nom_opt'] = 0
    biogas['total_cost'] = 0
    biogas.drop(columns=['capital_cost', 'marginal_cost'], inplace=True)

    biogas['annual_cost'] = biogas['annual_cost'].apply(lambda x: f"{int(x/1_000_000):,}".replace(',', ' ') + " MSEK/year")
    biogas['energy_produced'] = biogas['energy_produced'].apply(lambda x: f"{int(x/1_000):,}".replace(',', ' ') + " GWh/year")
    biogas['shadow_price'] = biogas['shadow_price'].apply(lambda x: f"{int(x):,}".replace(',', ' ') + " SEK/MWh")
    biogas = biogas[['p_nom_opt', 'lifetime', 'energy_produced', 'annual_cost', 'shadow_price', 'total_cost']]
    biogas.rename(columns=generator_column_names, inplace=True)

    other = NETWORK.links.loc[['H2 electrolysis', 'Battery charge']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt']]

    other['total_cost'] = np.where(other['p_nom_opt'] != 0, other['capital_cost'] * other['p_nom_opt'], 0)
    other['annual_cost'] = np.where(other['p_nom_opt'] != 0, other['total_cost'] / other['lifetime'], 0)
    other.drop(columns=['capital_cost', 'marginal_cost'], inplace=True)

    other['total_cost'] = other['total_cost'].apply(lambda x: int(f"{int(x/1_000_000):,}".replace(',', '')))
    other['annual_cost'] = other['annual_cost'].apply(lambda x: f"{int(x/1_000_000):,}".replace(',', ' ') + " MSEK/year")
    other['lifetime'] = other['lifetime'].apply(lambda x: f"{int(x)} years")
    other['p_nom_opt'] = other['p_nom_opt'].apply(lambda x: f"{int(x):,}".replace(',', ' ') + " MW")
    other = other[['p_nom_opt', 'lifetime', 'annual_cost', 'total_cost']]
    other.rename(columns=generator_column_names, inplace=True)

    stores = NETWORK.stores.loc[["H2 storage", "Battery"]][['capital_cost', 'marginal_cost', 'lifetime', 'e_nom_opt']]

    stores['total_cost'] = np.where(stores['e_nom_opt'] != 0, stores['capital_cost'] * stores['e_nom_opt'], 0)
    stores['annual_cost'] = np.where(stores['e_nom_opt'] != 0, stores['total_cost'] / stores['lifetime'], 0)
    stores.drop(columns=['capital_cost', 'marginal_cost'], inplace=True)

    stores['total_cost'] = stores['total_cost'].apply(lambda x: int(f"{int(x/1_000_000):,}".replace(',', '')))
    stores['annual_cost'] = stores['annual_cost'].apply(lambda x: f"{int(x/1_000_000):,}".replace(',', ' ') + " MSEK/year")
    stores['lifetime'] = stores['lifetime'].apply(lambda x: f"{int(x):,} years")
    stores['e_nom_opt'] = stores['e_nom_opt'].apply(lambda x: f"{int(x):,}".replace(',', ' ') + " MWh")
    stores = stores[['e_nom_opt', 'lifetime', 'annual_cost', 'total_cost']]
    stores.rename(columns=store_column_names, inplace=True)

    data = pd.concat([generators, biogas, other, stores])
    data.index = [labels[col] for col in data.index]
    data = data.fillna("")

    total_total_cost = int(data["Totalkostnad"].sum())

    st_obj.dataframe(data, column_config={
        "Totalkostnad": st.column_config.ProgressColumn(
            "Totalkostnad",
            help="Total kostnad med procent-andel av total",
            format="%f MSEK",
            min_value=0,
            max_value=total_total_cost,
        )
    })
