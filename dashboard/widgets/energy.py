import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from library.config import set_data_root
from widgets.utilities import round_and_prefix, round_and_prettify, scenario, gen_palette
import os.path
from library.language import TEXTS

def _plot_metrics_and_bar(
    metricName1, metric1,
    metricName2, metric2,
    x, y,
    max_value, color
):
    fig = plt.figure(figsize=(10, 3))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])

    ax0 = plt.subplot(gs[0])
    nameStyle = { "fontsize":20, "color": 'black', "ha": 'center', "va": 'center' }
    metricStyle = { "fontsize":50, "color": 'black', "ha": 'center', "va": 'center' }
    ax0.text(0.25, 1, metricName1, **nameStyle)
    ax0.text(0.75, 1, metricName2, **nameStyle)
    ax0.text(0.25, 0.5, metric1, **metricStyle)
    ax0.text(0.75, 0.5, metric2, **metricStyle)
    ax0.axis('off')

    ax1 = plt.subplot(gs[1])
    ax1.bar(x, y, color=color)
    ax1.set_ylim(0, max_value)
    ax1.axis('off')

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.2)

    st.pyplot(fig)

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
        with st.container():
            _plot_metrics_and_bar(
                "Nominal effect", "-",
                "Units required", "-",
                [], [], 
                max_value, gen_palette(generator))
        return

    power_t = pd.read_csv(fname, parse_dates=True)
    if resolution == '1M':
        power_t = power_t.iloc[1:]

    details = pd.read_csv(data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / generator / 'details.csv',index_col=0)

    with st.container():
        _plot_metrics_and_bar(
            TEXTS["Nominal effect"], round_and_prefix(details.loc['p_nom_opt'][generator],'M','W'),
            TEXTS["Units required"], round_and_prettify(details.loc['mod_units'][generator],generator),
            power_t['snapshot'].astype('str'), power_t[generator],
            max_value, gen_palette(generator)
        )
        st.write('\n' * 2) 
