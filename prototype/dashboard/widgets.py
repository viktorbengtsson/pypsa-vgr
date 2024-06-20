import streamlit as st
import numpy as np
import pandas as pd
from data_loading import network_data_from_variables

def render_gen_widget(st_obj, header, key, data, countSuffix, compare_data):
    with st_obj.container(border=True):
        st.title(header)
        if compare_data is None:
            capacity = data.loc[key, "p_nom_opt"].sum()
            count = data.loc[key, "generators"].sum()
            price = data.loc[key, "annual_cost"].sum() / data.loc[key, "energy_produced"].sum() / 1000 if data.loc[key, "energy_produced"].sum() > 0 else 0
            st.metric(f"{price:.2f} kr/kWh", f"{count:.0f} {countSuffix}", delta=f"{capacity:.0f} MW", delta_color="off")
        else:
            count = data.loc[key, "generators"].sum()
            compare_count = compare_data.loc[key, "generators"].sum()
            delta = count - compare_count
            st.metric("", f"{count:.0f} {countSuffix}", delta=f"{delta:.0f} {countSuffix}", label_visibility="collapsed")
def render_stor_widget(st_obj, header, key, data, compare_data):
    with st_obj.container(border=True):
        st.title(header)
        if compare_data is None:
            capacity = data.loc[key, "p_nom_opt"].sum() / 1_000
            price = data.loc[key, "annual_cost"].sum() / 1_000_000
            st.metric(f"{price:.0f} MSEK", f"{capacity:.1f} GW", delta="", delta_color="off")
        else:
            capacity = data.loc[key, "p_nom_opt"].sum() / 1_000
            compare_capacity = compare_data.loc[key, "p_nom_opt"].sum() / 1_000
            delta = capacity - compare_capacity
            st.metric("", f"{capacity:.1f} GW", delta=f"{delta:.1f} GW", label_visibility="collapsed")

def _get_data(config):
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

    return [generators, stores]

def render_widgets(st_obj, config, compare_config):
    st.markdown(
        f"""
        <style>
            h1 {{
                line-height: 1;
                font-size: 1em;
                padding: 0 0 0.5em 0;
                color: #888888;
                font-weight: normal;
                text-transform: uppercase;
            }}
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
                min-height: {10.25 if compare_config is None else 0}rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    [generators, stores] = _get_data(config)
    [generators_compare, stores_compare] = _get_data(compare_config) if compare_config is not None else [None, None]

    if compare_config is None:
        col1, col2, col3 = st_obj.columns([5,5,3], gap="small")

        render_gen_widget(col1, "Vindkraft (land)", ["Onwind park"], generators, "st", generators_compare)
        render_gen_widget(col2, "Vindkraft (hav)", ["Offwind park"], generators, "st", generators_compare)
        render_gen_widget(col1, "Solpark", ["Solar park"], generators, "ha", generators_compare)
        render_gen_widget(col2, "Biogas", ["Combined Cycle Gas turbine", "Simple Cycle Gas turbine"], generators, "st", generators_compare)
        render_gen_widget(col1, "Kärnkraft", ["Conventional nuclear", "SMR nuclear"], generators, "st", generators_compare)

        render_stor_widget(col3, "Vätgas", ["H2 storage"], stores, stores_compare)
        render_stor_widget(col3, "Batteri", ["Battery storage"], stores, stores_compare)
    else:
        col1, col2, col3, col4 = st_obj.columns([1,1,1,1], gap="small")

        render_gen_widget(col1, "Vindkraft (land)", ["Onwind park"], generators, "st", generators_compare)
        render_gen_widget(col2, "Vindkraft (hav)", ["Offwind park"], generators, "st", generators_compare)
        render_gen_widget(col3, "Solpark", ["Solar park"], generators, "ha", generators_compare)
        render_gen_widget(col4, "Biogas", ["Combined Cycle Gas turbine", "Simple Cycle Gas turbine"], generators, "st", generators_compare)
        render_gen_widget(col1, "Kärnkraft", ["Conventional nuclear", "SMR nuclear"], generators, "st", generators_compare)

        render_stor_widget(col3, "Vätgas", ["H2 storage"], stores, stores_compare)
        render_stor_widget(col4, "Batteri", ["Battery storage"], stores, stores_compare)
