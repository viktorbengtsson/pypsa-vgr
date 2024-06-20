import streamlit as st
import numpy as np
import pandas as pd
from data_loading import network_data_from_variables

def render_gen_widget(st_obj, header, key, data, countSuffix):
    with st_obj.container(border=True):
        st.title(header)
        capacity = data.loc[key, "p_nom_opt"].sum()
        count = data.loc[key, "generators"].sum()
        price = data.loc[key, "annual_cost"].sum() / data.loc[key, "energy_produced"].sum() / 1000 if data.loc[key, "energy_produced"].sum() > 0 else 0
        st.metric(f"{price:.2f} kr/kWh", f"{count:.0f} {countSuffix}", delta=f"{capacity:.0f} MW", delta_color="off")
def render_stor_widget(st_obj, header, key, data):
    with st_obj.container(border=True):
        st.title(header)
        capacity = data.loc[key, "p_nom_opt"].sum() / 1_000
        price = data.loc[key, "annual_cost"].sum() / 1_000_000
        st.metric(f"{price:.0f} MSEK", f"{capacity:.0f} GW", delta="", delta_color="off")

def render_widgets(st_obj, config):
    st.markdown(
        """
        <style>
            h1 {
                line-height: 1;
                font-size: 1em;
                padding: 0 0 0.5em 0;
                color: #888888;
                font-weight: normal;
                text-transform: uppercase;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
                max-width: 14rem;
                min-height: 10.25rem;
                margin-top: -1em;
                margin-bottom: 1em;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    NETWORK = network_data_from_variables("../", config)
    parameters = pd.read_csv("../../data/assumptions.csv")
    parameters.set_index(['technology', 'parameter'], inplace=True)

    generator_index = NETWORK.generators.index.difference(['Backstop', 'Biogas input'])

    if NETWORK.generators["p_nom_opt"].sum() == 0:
        return

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

    spacer1, col1, col2, col3, spacer2 = st_obj.columns([3,10,10,6,2], gap="small")

    render_gen_widget(col1, "Vindkraft (land)", ["Onwind park"], generators, "st")
    render_gen_widget(col2, "Vindkraft (hav)", ["Offwind park"], generators, "st")
    render_gen_widget(col1, "Solpark", ["Solar park"], generators, "ha")
    render_gen_widget(col2, "Biogas", ["Combined Cycle Gas turbine", "Simple Cycle Gas turbine"], generators, "st")
    render_gen_widget(col1, "Kärnkraft", ["Conventional nuclear", "SMR nuclear"], generators, "st")

    render_stor_widget(col3, "Vätgas", ["H2 storage"], stores)
    render_stor_widget(col3, "Batteri", ["Battery storage"], stores)
