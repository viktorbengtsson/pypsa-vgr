import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from library.config import set_data_root
from widgets.utilities import scenario, round_and_prefix
from library.language import TEXTS, LANGUAGE, MONTHS
from widgets.comparison import comparison_widget
from pathlib import Path

def ambition_level(sufficiency_target):
    if sufficiency_target > 0.9: return TEXTS["very high"]
    if sufficiency_target > 0.75: return TEXTS["high"]
    if sufficiency_target > 0.5: return TEXTS["moderate"]
    if sufficiency_target > 0.25: return TEXTS["quite modest"]
    return TEXTS["fairly low"]

def import_level(import_ratio):
    if import_ratio < 0.02: return TEXTS["almost no"]
    if import_ratio < 0.05: return TEXTS["extremely little"]
    if import_ratio < 0.1: return TEXTS["a small amount"]
    if import_ratio < 0.2: return TEXTS["a moderate amount"]
    if import_ratio < 0.5: return TEXTS["a large amount"]
    return TEXTS["more than half of the"]

def sufficiency_metrics(data):
    data['month'] = MONTHS
    data['value'] = data['value'].round(2)
    return ", ".join(data[data['value'] == 1.0]['month']), f"{data[data['value'] < 1.0]['value'].mean():.1%}"



def explainer_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, modal):
    data_root = set_data_root()
    resolution = '1M'
    performance_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / "performance_metrics.csv.gz"
    sufficiency_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'performance' / f"sufficiency_t_{resolution}.csv.gz"
    solar_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / 'solar' / 'details.csv.gz'
    onwind_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'generators' / 'onwind' / 'details.csv.gz'
    land_path = data_root / scenario(geo, target_year, floor, load_target, h2, offwind, biogas_limit) / 'landuse.csv.gz'

    if performance_path.is_file():
        performance = pd.read_csv(performance_path, compression='gzip')
        performance.rename(columns={'Unnamed: 0': 'type'}, inplace=True)
        performance.set_index('type', inplace=True)

    if sufficiency_path.is_file():
        sufficiency = pd.read_csv(sufficiency_path, compression='gzip', parse_dates=True, index_col='snapshot')
        sufficiency.rename(columns={'0': 'value'}, inplace=True)

    sufficient_months, average_outside_full = sufficiency_metrics(sufficiency)

    if solar_path.is_file():
        solar_details = pd.read_csv(solar_path, compression='gzip', index_col=0)
    if onwind_path.is_file():
        onwind_details = pd.read_csv(onwind_path, compression='gzip', index_col=0)
    if land_path.is_file():
        land_use = pd.read_csv(land_path, compression='gzip', index_col=0)

    area_per_turbine = 20

    total_land = float(land_use.loc['total landareal', geo.split('-',1)[-1]])
    built_land = float(land_use.loc['bebyggd och anlagd mark ', geo.split('-',1)[-1]])
    solar_land_percentage = float(solar_details.loc['mod_units','solar']) / built_land
    onwind_land_percentage = float(onwind_details.loc['mod_units','onwind']) * area_per_turbine / built_land

    text_path = Path(__file__).parent / f"explainer_{LANGUAGE}.md"
    body = (text_path).read_text(encoding='utf-8').format(
        #sufficiency_target = f"{floor:.0%}",
        sufficiency_target = f"{load_target/15:.0%}", # TODO: Remove this temporary fix
        demand_target = load_target,
        year = target_year,
        ambition_level = ambition_level(floor),
        import_level = import_level(performance.loc['Shortfall', 'Value']),
        suffciency = f"{performance.loc['Sufficiency', 'Value']:.1%}",
        full_months = sufficient_months,
        average_sufficiency_outside_full = average_outside_full,
        super_power = round_and_prefix(performance.loc['Curtailed energy', 'Value'], 'M', 'Wh', 0),
        total_area = f"{total_land:,.0f} ha",
        built_area = f"{built_land:,.0f} ha",
        solar_area_percentage = f"{solar_land_percentage:.2%}",
        onwind_area_percentage = f"{onwind_land_percentage:.2%}"
    )
    with st.container():
        st.markdown(body)
        comparison_widget(geo, target_year, floor, load_target, h2, offwind, biogas_limit, modal)
