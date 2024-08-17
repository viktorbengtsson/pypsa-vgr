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
from widgets.controls import controls_widget, controls_readonly_widget

# State management
data_root = set_data_root()
default_main_geo = "14" #VGR
default_geo_level = "0" #Län

if "clear-cache" in st.query_params and st.query_params["clear-cache"] == "true":
    clear_cache()

initial_load = False
if 'main_geo' not in st.session_state or 'geo_level' not in st.session_state or 'geo' not in st.session_state or 'variables' not in st.session_state:
    initial_load = True
    st.session_state['main_geo'] = default_main_geo if not "main_geo" in st.query_params or st.query_params.main_geo is None or st.query_params.main_geo == "" else st.query_params.main_geo
    st.session_state['geo_level'] = default_geo_level if not "geo_level" in st.query_params or st.query_params.geo_level is None or st.query_params.geo_level == "" else st.query_params.geo_level
    st.session_state['geo'] = "" if not "geo" in st.query_params or st.query_params.geo is None or st.query_params.geo == "" else st.query_params.geo
    st.session_state['variables'] = get_default_variables(data_root)
    st.session_state['compare_variables'] = None

main_geo = st.session_state['main_geo']
geo_level = st.session_state['geo_level']
geo = st.session_state['geo']
variables = st.session_state['variables']
compare_variables = st.session_state['compare_variables']

st.markdown("""
    <style>
        button {
            padding: 0.125rem 0.375rem !important;
            min-height: 1.5rem !important;
        }
        button div p {
            font-size: 11px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Define columns
sidebar = st.sidebar
col1, col2 = st.columns([3, 1], gap="small")

# Show map selector and selection widget in sidebar
with sidebar:
    available_geo, main_geo = main_geo_selector(main_geo)
    if initial_load:
        geo = streamlit_map_selector(main_geo=main_geo, available_geo=available_geo, initial_geo=geo)
    else:
        geo = streamlit_map_selector(main_geo=main_geo, available_geo=available_geo, initial_geo=None)

    if geo is None:
        st.stop()   # Not sure why map_selector returns None on the initial render

    controls = st.container()
    with controls:
        tmp = st.empty()
        compare = tmp.button('Jämför')
        if compare:
            tmp.empty()
            close_compare = tmp.button('Stäng jämförelse')
            compare_variables = variables
            colA, colB = st.columns([1,6], gap="small")
            controls = colB
            with colA:
                controls_readonly_widget(compare_variables)
        else:
            compare_variables = None

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


# Persist session values and query string
st.query_params["main_geo"] = main_geo
st.query_params["geo_level"] = geo_level
st.query_params["geo"] = geo
st.query_params["variables"] = ','.join(map(str, variables))

st.session_state['geo_level'] = geo_level
st.session_state['main_geo'] = main_geo
st.session_state['geo'] = geo
st.session_state['variables'] = variables
st.session_state['compare_variables'] = compare_variables
