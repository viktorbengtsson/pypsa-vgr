import streamlit as st
import sys
import pandas as pd
from library.config import set_data_root
from widgets.utilities import round_and_prefix, round_and_format, round_and_percentage, scenario, stor_palette, gen_palette, full_palette
import os.path
from library.language import TEXTS
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths

color_mapping = full_palette()

def _html_wrapper(name, metrics, color):
    fname = paths.dashboard_path / 'widgets' / "energy.html"

    with open(fname, 'r') as file:
        html = file.read()

    html = html.replace('{name}', name)
    html = html.replace('{color}', color)
    for idx in range(0,3):
        if len(metrics) > idx:
            metric = metrics[idx]
            html = html.replace(f'{{metric_{idx}_key}}', metric["key"])
            html = html.replace(f'{{metric_{idx}_value}}', metric["value"])
        else:
            html = html.replace(f'{{metric_{idx}_key}}', "")
            html = html.replace(f'{{metric_{idx}_value}}', "")

    st.markdown(html, unsafe_allow_html=True)

def _safely_load_data(path, generator):
    if not os.path.isfile(path):
        return [
            { "key": TEXTS["Effect"], "value": "-" },
            { "key": TEXTS[f"units_required_{generator}"], "value": "-" },
            { "key": TEXTS["fraction_energy"], "value": "-" }
        ]
    else:
        details = pd.read_csv(path, compression='gzip', index_col=0)
        return [
            { "key": TEXTS["Effect"], "value": round_and_prefix(details.loc['p_nom_opt'][generator],'M','W', 0) },
            { "key": TEXTS[f"units_required_{generator}"], "value": round_and_format(details.loc['mod_units'][generator]) },
            { "key": TEXTS["fraction_energy"], "value": f"{round_and_format(details.loc['fraction_energy'][generator] * 100)}{'%' if details.loc['fraction_energy'][generator] != 0 else ''}" }
        ]

def energy_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, generator, modal):
    # State management
    data_root = set_data_root()
    data_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / 'details.csv.gz'
    metrics = _safely_load_data(data_path, generator)

    with st.container(border=True):
        col1, col2 = st.columns([3,1])
        col1.markdown(f'<div style="font-size:16px; margin-bottom: 10px;"><div style="background-color: {gen_palette(generator)}; opacity: {color_mapping["opacity"]}; width: 10px; height: 10px; display: inline-block; margin-right: 5px;"></div><span>{TEXTS[generator]}</span>', unsafe_allow_html=True)
        if col2.button(":material/help:", key=generator):
            modal(generator)
        _html_wrapper(TEXTS[generator], metrics, gen_palette(generator))

def store_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, store, modal):
    # State management
    data_root = set_data_root()
    data_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'stores' / store / 'details.csv.gz'

    if not os.path.isfile(data_path):
        metrics = [
            { "key": TEXTS["Capacity"], "value": "-" },
            { "key": TEXTS["Effect"], "value": "-" },
            { "key": TEXTS["fraction_energy"], "value": "-"}
        ]
    else:
        details = pd.read_csv(data_path, compression='gzip', index_col=0)
        metrics = [
            { "key": TEXTS["Capacity"], "value": round_and_prefix(float(details.loc['e_nom_opt'][store]),'M','Wh', 0) },
            { "key": TEXTS["Effect"], "value": round_and_prefix(float(details.loc['p_nom_opt_discharge'][store]),'M','W', 0) if round(float(details.loc['e_nom_opt'][store]),9) != 0 else '-' },
            { "key": TEXTS["fraction_stored_energy"], "value": round_and_percentage(details.loc['fraction_energy_out'][store])}
        ]

    with st.container(border=True):
        col1, col2 = st.columns([3,1])
        col1.markdown(f'<div style="font-size:16px; margin-bottom: 10px;"><div style="background-color: {gen_palette(store)}; opacity: {color_mapping["opacity"]}; width: 10px; height: 10px; display: inline-block; margin-right: 5px;"></div><span>{TEXTS[store]}</span>', unsafe_allow_html=True)
        if col2.button(":material/help:", key=store):
            modal(store)
        _html_wrapper(TEXTS[store], metrics, stor_palette(store))

def backstop_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, modal):
    # State management
    data_root = set_data_root()
    details = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / "backstop" / 'details.csv.gz', compression='gzip', index_col=0)
    metrics = [
        { "key": TEXTS["total_energy"], "value": round_and_prefix(details.loc['total_energy']["backstop"],'M','Wh', 0) },
    ]

    with st.container(border=True):
        col1, col2 = st.columns([3,1])
        col1.markdown(f'<div style="font-size:16px; margin-bottom: 10px;"><div style="background-color: {gen_palette("backstop")}; opacity: {color_mapping["opacity"]}; width: 10px; height: 10px; display: inline-block; margin-right: 5px;"></div><span>{TEXTS["backstop"]}</span>', unsafe_allow_html=True)
        if col2.button(":material/help:", key='backstop'):
            modal('backstop')
        _html_wrapper(TEXTS["backstop"], metrics, gen_palette("backstop"))
