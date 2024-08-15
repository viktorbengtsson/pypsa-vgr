import streamlit as st
from library.config import set_data_root, clear_cache, get_default_variables
#from MapSelector.map_selector.map_selector import streamlit_map_selector
from map_selector.map_selector import streamlit_map_selector
from widgets.geo import main_geo_selector
from widgets.production import big_chart_widget
from widgets.sufficiency import sufficiency_widget
from widgets.comparison import comparison_widget
from widgets.price import price_widget
from widgets.energy import energy_widget
from widgets.controls import controls_widget

# State management
data_root = set_data_root()
default_main_geo = "14" #VGR

if "clear-cache" in st.query_params and st.query_params["clear-cache"] == "true":
    clear_cache()

if 'main_geo' not in st.session_state:
    st.session_state['main_geo'] = default_main_geo if not "main_geo" in st.query_params or st.query_params.main_geo is None or st.query_params.main_geo == "" else st.query_params.main_geo
if 'geo' not in st.session_state:
    st.session_state['geo'] = "" if not "geo" in st.query_params or st.query_params.geo is None or st.query_params.geo == "" else st.query_params.geo
if 'variables' not in st.session_state:
    st.session_state['variables'] = get_default_variables(data_root)

main_geo = st.session_state['main_geo']
geo = st.session_state['geo']
variables = st.session_state['variables']

# Define columns
sidebar = st.sidebar
col1, col2 = st.columns([3, 1], gap="small")

# Show map selector and selection widget in sidebar
with sidebar:
    available_geo, main_geo = main_geo_selector(main_geo)
    geo = streamlit_map_selector(main_geo=main_geo, available_geo=available_geo, initial_geo=geo)

    if geo is None:
        st.stop()   # Not sure why map_selector returns None on the initial render

    controls = sidebar.container()
    with controls:
        variables = controls_widget(variables)

with col1:
    big_chart_widget(geo=geo, **variables, generators=['solar', 'onwind', 'offwind', 'backstop'])
    col11, col12 = col1.columns(2)
    with col11:
        sufficiency_widget()
    with col12:
        comparison_widget()
        price_widget()


with col2:
    energy_widget(geo=geo, **variables, generator='solar')
    energy_widget(geo=geo, **variables, generator='onwind')
    energy_widget(geo=geo, **variables, generator='offwind')
    energy_widget(geo=geo, **variables, generator='biogas_market')

# The right-side column holds energy widgets


# Persist session values in query string
st.query_params["main_geo"] = main_geo
st.query_params["geo"] = geo
st.query_params["variables"] = ','.join(map(str, variables))