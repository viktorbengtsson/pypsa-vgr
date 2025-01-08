import streamlit as st
from pathlib import Path
from library.config import clear_cache, get_default_variables#, set_data_root
from MapSelector.map_selector.map_selector import streamlit_map_selector
#from MapSelector.map_selector import streamlit_map_selector
from widgets.geo import main_geo_selector
from widgets.consumption import big_chart_widget
from widgets.performance import performance_widget
from widgets.explainer import explainer_widget
from widgets.price import price_widget
from widgets.cards import renewable_widget, biogas_widget, store_widget, backstop_widget
from widgets.controls import controls_widget, controls_readonly_widget
from library.language import TEXTS, LANGUAGE

# State management
#data_root = set_data_root()
default_main_geo = "14" #VGR

if "clear-cache" in st.query_params and st.query_params["clear-cache"] == "true":
    clear_cache()

if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False

initial_load = False
if 'main_geo' not in st.session_state or 'geo' not in st.session_state or 'variables' not in st.session_state:
    initial_load = True

    st.session_state['main_geo'] = default_main_geo if not "main_geo" in st.query_params or st.query_params.main_geo is None or st.query_params.main_geo == "" else st.query_params.main_geo
    st.session_state['geo'] = "" if not "geo" in st.query_params or st.query_params.geo is None or st.query_params.geo == "" else st.query_params.geo
    st.session_state['variables'] = get_default_variables(st.query_params)
    st.session_state['compare_variables'] = None

main_geo = st.session_state['main_geo']
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

# The welcome modal dialog
@st.dialog(TEXTS["Welcome"])
def welcome():
    # Load page data
    content_path = Path(__file__).parent / 'content'
    body = (content_path / f"welcome_{LANGUAGE}.md").read_text(encoding='utf-8')
    st.markdown(body)

# The help modal dialog
@st.dialog(TEXTS["explainer_heading"])
def help(location):
    # Load page data
    content_path = Path(__file__).parent / 'content/help'
    body = (content_path / f"{location}_{LANGUAGE}.md").read_text(encoding='utf-8')
    st.markdown(body)


# Define columns
sidebar = st.sidebar
col1, col2 = st.columns([3, 1], gap="small")

# Show map selector and selection widget in sidebar
with sidebar:
    available_geo, main_geo = main_geo_selector(main_geo)
    #if initial_load:
    geo = streamlit_map_selector(main_geo=main_geo, available_geo=available_geo, initial_geo=None)
    #else:
    #    geo = streamlit_map_selector(main_geo=main_geo, available_geo=available_geo, initial_geo=None)

    if geo is None:
        st.stop()   # Not sure why map_selector returns None on the initial render

    controls = st.container()
    with controls:
        tmp = st.empty()
        #compare = tmp.button(TEXTS["Compare"])
        #if compare:
        #    tmp.empty()
        #    close_compare = tmp.button(TEXTS["Close compare"])
        #    compare_variables = variables
        #    colA, colB = st.columns([1,4], gap="small")
        #    controls = colB
        #    with colA:
        #        controls_readonly_widget(compare_variables)
        #else:
        compare_variables = None

    with controls:
        variables = controls_widget(variables)

    footer = st.container()

    with footer:
        content_path = Path(__file__).parent / 'content'
        footer = (content_path / f"footer_{LANGUAGE}.md").read_text(encoding='utf-8')
        st.divider()
        st.markdown(footer)

with col1:
    big_chart_widget(geo=geo, **variables, modal=help)
    col11, col12 = col1.columns([5,6])
    with col11:
        performance_widget(geo=geo, **variables, modal=help)
        price_widget(geo=geo, **variables, modal=help)
    with col12:
        explainer_widget(geo=geo, **variables, modal=help)
        #comparison_widget(geo=geo, **variables, modal=help)
        # stores_widget(geo=geo, **variables)

with col2:
    #legends()
    renewable_widget(geo=geo, **variables, generator='solar', modal=help)
    renewable_widget(geo=geo, **variables, generator='onwind', modal=help)
    if variables['offwind']:
        renewable_widget(geo=geo, **variables, generator='offwind', modal=help)
    biogas_widget(geo=geo, **variables, modal=help)
    store_widget(geo=geo, **variables, store='battery', modal=help)
    if variables['h2']:
        store_widget(geo=geo, **variables, store='h2', modal=help)
    backstop_widget(geo=geo, **variables, modal=help)

if not st.session_state.popup_shown:
    welcome()
    st.session_state.popup_shown = True

# The right-side column holds energy widgets

# Persist session values and query string
st.query_params["main_geo"] = main_geo
st.query_params["geo"] = geo
for key in variables:
    st.query_params[key] = str(variables[key])

st.session_state['main_geo'] = main_geo
st.session_state['geo'] = geo
st.session_state['variables'] = variables
st.session_state['compare_variables'] = compare_variables

#cookieState = {
#    "main_geo": main_geo,
#    "geo": geo,
#    "variables": variables,
#    "compare_variables": compare_variables
#}
