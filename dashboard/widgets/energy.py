import streamlit as st
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from library.config import set_data_root
from widgets.utilities import round_and_prefix, round_and_format, scenario, stor_palette, gen_palette
import os.path
from library.language import TEXTS
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths

def _plot_metrics_and_bar(
    name,
    metrics,
    x, y,
    max_value, color
):
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

def _energy_max_value(geo, target_year, floor, load_target, h2, offwind, biogas_limit, generator):
    # State management
    data_root = set_data_root()

    resolution = '1M'
    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv.gz"
    if os.path.isfile(fname):
        power_t = pd.read_csv(fname, compression='gzip', parse_dates=True)
        if resolution == '1M':
            power_t = power_t.iloc[1:]
        return power_t[generator].max()
    
    return 0

def energy_max_value(geo, target_year, floor, load_target, h2, offwind, biogas_limit, generators):
    results = [_energy_max_value(geo, target_year, floor, load_target, h2, offwind, biogas_limit, gen) for gen in generators]

    return max(results)

def energy_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, max_value, generator):
    # State management
    data_root = set_data_root()

    resolution = '1M'
    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv.gz"
    if not os.path.isfile(fname):
        with st.container(border=True):
            metrics = [
                { "key": TEXTS["Effect"], "value": "-" },
                { "key": TEXTS[f"units_required_{generator}"], "value": "-" },
                { "key": TEXTS["curtailment"], "value": "-" }
            ]
            _plot_metrics_and_bar(
                TEXTS[generator],
                metrics,
                [], [], 
                max_value, gen_palette(generator))
        return

    power_t = pd.read_csv(fname, compression='gzip', parse_dates=True)
    if resolution == '1M':
        power_t = power_t.iloc[1:]

    details = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / 'details.csv.gz', compression='gzip', index_col=0)

    with st.container(border=True):
        metrics = [
            { "key": TEXTS["Effect"], "value": round_and_prefix(details.loc['p_nom_opt'][generator],'M','W') },
            { "key": TEXTS[f"units_required_{generator}"], "value": round_and_format(details.loc['mod_units'][generator]) },
            { "key": TEXTS["curtailment"], "value": round_and_format(details.loc['fraction_energy'][generator] * 100) }
        ]
        _plot_metrics_and_bar(
            TEXTS[generator],
            metrics,
            power_t['snapshot'].astype('str'), power_t[generator],
            max_value, gen_palette(generator)
        )

def store_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, max_value, stores):
    # State management
    data_root = set_data_root()

    for store in stores:
        with st.container(border=True):
            metrics = []
            fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'stores' / store / 'details.csv.gz'
            if not os.path.isfile(fname):
                return
            else:
                details = pd.read_csv(fname, compression='gzip', index_col=0)
                print(details.loc['e_nom_opt'][store])
                metrics.append({ "key": TEXTS["Capacity"], "value": round_and_prefix(float(details.loc['e_nom_opt'][store]),'M','Wh') })

            _plot_metrics_and_bar(
                TEXTS[store],
                metrics,
                None, None,
                None, stor_palette(store)
            )

def backstop_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit):
    # State management
    data_root = set_data_root()

    resolution = '1M'
    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / 'backstop' / f"power_t_{resolution}.csv.gz"
    if not os.path.isfile(fname):
        with st.container(border=True):
            metrics = [
                { "key": TEXTS["Effect"], "value": "-" }
            ]
            _plot_metrics_and_bar(
                TEXTS["backstop"],
                metrics,
                [], [], 
                None, gen_palette("backstop"))
        return

    power_t = pd.read_csv(fname, compression='gzip', parse_dates=True)
    if resolution == '1M':
        power_t = power_t.iloc[1:]

    details = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / "backstop" / 'details.csv.gz', compression='gzip', index_col=0)

    with st.container(border=True):
        metrics = [
            { "key": TEXTS["Effect"], "value": round_and_prefix(details.loc['p_nom_opt']["backstop"],'M','W') },
        ]
        _plot_metrics_and_bar(
            TEXTS["backstop"],
            metrics,
            power_t['snapshot'].astype('str'), power_t["backstop"],
            None, gen_palette("backstop")
        )
