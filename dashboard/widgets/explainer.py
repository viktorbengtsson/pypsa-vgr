import streamlit as st
import pandas as pd
import math
import json
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

def cf_level(cf):
    if cf > 0.9: return TEXTS["very high"]
    if cf > 0.8: return TEXTS["high"]
    if cf > 0.7: return TEXTS["moderate"]
    if cf > 0.6: return TEXTS["fairly low"]
    return TEXTS["very low"]

def sufficiency_metrics(data):
    data['month'] = MONTHS
    data['value'] = data['value'].round(2)
    full_months = data[data['value'] == 1.0]
    if len(full_months) > 0:
        return ", ".join(data[data['value'] == 1.0]['month']), f"{data[data['value'] < 1.0]['value'].mean():.1%}"
    else:
        return '',''

def full_months_text(fm):
    if len(fm) > 0:
        return TEXTS['the demand is fully met']
    else:
        return TEXTS['The demand is not fully met during any month']
    
def explainer_widget(geo, target_year, self_sufficiency, h2, offwind, biogas_limit, modal):
    data_path = set_data_root() / scenario(geo, target_year, self_sufficiency, h2, offwind, biogas_limit)
    resolution = '1M'
    performance_path = data_path / 'performance' / "performance_metrics.csv.gz"
    sufficiency_path = data_path / 'performance' / f"sufficiency_t_{resolution}.csv.gz"
    solar_path = data_path / 'generators' / 'solar' / 'details.csv.gz'
    onwind_path = data_path / 'generators' / 'onwind' / 'details.csv.gz'
    biogas_turbine_path = data_path / 'generators' / 'biogas-turbine' / 'details.csv.gz'
    land_path = data_path / 'landuse.csv.gz'
    config_path = data_path / 'config.json'

    with config_path.open('r') as cf:
        config = json.load(cf)

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
    if biogas_turbine_path.is_file():
        biogas_turbine_details = pd.read_csv(biogas_turbine_path, compression='gzip', index_col=0)
    if land_path.is_file():
        land_use = pd.read_csv(land_path, compression='gzip', index_col=0)

    area_per_turbine = 20

    total_land = float(land_use.loc['total landareal', geo.split('-',1)[-1]])
    built_land = float(land_use.loc['bebyggd och anlagd mark ', geo.split('-',1)[-1]])
    solar_land_percentage = float(solar_details.loc['mod_units','solar']) / built_land
    onwind_land_percentage = float(onwind_details.loc['mod_units','onwind']) * area_per_turbine / built_land
    solar_land_percentage_total = float(solar_details.loc['mod_units','solar']) / total_land
    onwind_land_percentage_total = float(onwind_details.loc['mod_units','onwind']) * area_per_turbine / total_land

    text_path = Path(__file__).parent / f"explainer_{LANGUAGE}.md"
    body = (text_path).read_text(encoding='utf-8').format(
        geography = config['scenario']['geography-name'],
        target = round_and_prefix(performance.loc['Total energy','Value'], 'M', 'Wh', 0),
        year = target_year,
        sufficiency_target = f"{self_sufficiency:.1%}",
        ambition_level = ambition_level(self_sufficiency),
        sufficiency = f"{performance.loc['Sufficiency', 'Value']:.1%}",
        full_months = sufficient_months,
        full_months_text = full_months_text(sufficient_months),
        average_sufficiency_outside_full_text = TEXTS['average_sufficiency_outside_full_text'] if len(sufficient_months) > 0 else '',
        average_sufficiency_outside_full = average_outside_full,
        super_power = round_and_prefix(performance.loc['Curtailed energy', 'Value'], 'M', 'Wh', 0),
        solar_cf = f"{1 - solar_details.loc['curtailment', 'solar']:.1%}",
        solar_cf_level = cf_level(1- solar_details.loc['curtailment', 'solar']),
        onwind_cf = f"{1 - onwind_details.loc['curtailment', 'onwind']:.1%}",
        onwind_cf_level = cf_level(1- onwind_details.loc['curtailment', 'onwind']),
        gas_turbine_text1 = TEXTS['gas_turbine_text1'] if not math.isnan(biogas_turbine_details.loc['curtailment', 'biogas-turbine']) else '',
        gas_turbine_text2 = TEXTS['gas_turbine_text2'] if not math.isnan(biogas_turbine_details.loc['curtailment', 'biogas-turbine']) else '',
        biogas_turbine_cf = f"{1 - biogas_turbine_details.loc['curtailment', 'biogas-turbine']:.1%}" if not math.isnan(biogas_turbine_details.loc['curtailment', 'biogas-turbine']) else '',
        solar_area_percentage = f"{solar_land_percentage:.2%}",
        solar_area_percentage_total = f"{solar_land_percentage_total:.2%}",
        built_area = f"{built_land:,.0f} ha",
        total_area = f"{total_land:,.0f} ha",
        onwind_area_percentage = f"{onwind_land_percentage:.2%}",
        onwind_area_percentage_total = f"{onwind_land_percentage_total:.2%}",
    )
    with st.container():
        st.markdown(body)
        comparison_widget(geo, target_year, self_sufficiency, h2, offwind, biogas_limit, modal)
