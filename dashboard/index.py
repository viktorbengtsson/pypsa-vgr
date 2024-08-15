import streamlit as st
from library.config import set_data_root, clear_cache, get_default_variables
from MapSelector.map_selector.map_selector import custom_map_selector
from widgets.production import big_chart_widget
from widgets.sufficiency import sufficiency_widget
from widgets.comparison import comparison_widget
from widgets.price import price_widget
from widgets.energy import energy_widget

# State management
data_root = set_data_root()

if "clear-cache" in st.query_params and st.query_params["clear-cache"] == "true":
    clear_cache()

if 'geography' not in st.session_state:
    st.session_state['geography'] = [] if not "geography" in st.query_params or st.query_params.geography is None or st.query_params.geography == "" else st.query_params.geography.split(",")
if 'variables' not in st.session_state:
    st.session_state['variables'] = get_default_variables(data_root)

geography = st.session_state['geography']
variables = st.session_state['variables']

geo = 14
target_year = 2035
floor = 0.5
load_target = 19
h2 = True
offwind = True
biogas_limit = 500

# Define columns
sidebar = st.sidebar
col1, col2 = st.columns([3, 1], gap="small")

# Show map selector and selection widget in sidebar
with sidebar:
    geography = custom_map_selector(default=geography)
    controls = sidebar.container()
    with controls:
        controls.write("There will be controls here")

with col1:
    #if len(geography) == 0:
    #    st.write("VÄLJ KOMMUNER TILL VÄNSTER")
    #else:
    big_chart_widget(geo=geo, year=target_year, floor=floor, load=load_target, h2=h2, offwind=offwind, biogas=biogas_limit, generators=['solar', 'onwind', 'offwind', 'backstop'])
    col11, col12 = col1.columns(2)
    with col11:
        sufficiency_widget()
    with col12:
        comparison_widget()
        price_widget()

with col2:
    #if not len(geography) == 0:
    energy_widget(geo=geo, year=target_year, floor=floor, load=load_target, h2=h2, offwind=offwind, biogas=biogas_limit, generator='solar')
    energy_widget(geo=geo, year=target_year, floor=floor, load=load_target, h2=h2, offwind=offwind, biogas=biogas_limit, generator='onwind')
    energy_widget(geo=geo, year=target_year, floor=floor, load=load_target, h2=h2, offwind=offwind, biogas=biogas_limit, generator='offwind')
    energy_widget(geo=geo, year=target_year, floor=floor, load=load_target, h2=h2, offwind=offwind, biogas=biogas_limit, generator='biogas_market')

# The right-side column holds energy widgets
