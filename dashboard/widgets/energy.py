import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from library.config import set_data_root
from widgets.utilities import round_and_prefix, round_and_format, scenario, gen_palette
import os.path
from library.language import TEXTS

def _plot_metrics_and_bar(
    name,
    metrics,
    x, y,
    max_value, color
):
    st.markdown(f'<p style="font-size:16px;">{name}</p>', unsafe_allow_html=True)
    fig = plt.figure(figsize=(12, 2))

    #gs = gridspec.GridSpec(3, 2, height_ratios=[1, 1, 1], width_ratios=[3,1])
    #ax0 = plt.subplot(gs[:3, 0])
    #ax0.bar(x, y, color=color)
    #ax0.set_ylim(0, max_value)
    #ax0.axis('off')

    gs = gridspec.GridSpec(1, len(metrics))

    for idx, metric in enumerate(metrics):
        ax = plt.subplot(gs[0, idx])
        nameStyle = { "fontsize":33, "color": 'gray', "ha": 'center', "va": 'center' }
        metricStyle = { "fontsize":60, "color": 'black', "ha": 'center', "va": 'center' }
        ax.text(0.5, 1.0, metric["key"], **nameStyle)
        ax.text(0.5, 0.0, metric["value"], **metricStyle)
        ax.axis('off')

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.0)

    st.pyplot(fig)
    st.write("")

def _energy_max_value(geo, target_year, floor, load_target, h2, offwind, biogas_limit, generator):
    # State management
    data_root = set_data_root()

    resolution = '1M'
    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv"
    if os.path.isfile(fname):
        power_t = pd.read_csv(fname, parse_dates=True)
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
    fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / f"power_t_{resolution}.csv"
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

    power_t = pd.read_csv(fname, parse_dates=True)
    if resolution == '1M':
        power_t = power_t.iloc[1:]

    details = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / 'details.csv',index_col=0)

    with st.container(border=True):
        metrics = [
            { "key": TEXTS["Effect"], "value": round_and_prefix(details.loc['p_nom_opt'][generator],'M','W') },
            { "key": TEXTS[f"units_required_{generator}"], "value": round_and_format(details.loc['mod_units'][generator]) },
            { "key": TEXTS["curtailment"], "value": round_and_format(details.loc['curtailment'][generator] * 100) }
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

    metrics = []
    for store in stores:
        fname = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'stores' / store / 'details.csv'
        if not os.path.isfile(fname):
            return
        else:
            details = pd.read_csv(fname,index_col=0)
            metrics.append({ "key": TEXTS[store], "value": round_and_prefix(details.loc['e_nom_opt'][store],'M','Wh') })

    with st.container(border=True):
        _plot_metrics_and_bar(
            TEXTS["Stores"],
            metrics,
            None, None,
            None, None
        )
