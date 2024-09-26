import streamlit as st
from map_selector import streamlit_map_selector

geo = streamlit_map_selector(
    main_geo="14",
    initial_geo="1488",
    available_geo=["14", "1488"],
    country="sweden",
)
st.write("Selection in map: %s" % geo)
