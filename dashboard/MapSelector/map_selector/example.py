import streamlit as st
from map_selector import streamlit_map_selector

geo = streamlit_map_selector(
    main_geo="14",
    initial_geo="1480",
    available_geo=["14", "1480"],
    country="sweden",
)
st.write("Selection in map: %s" % geo)
