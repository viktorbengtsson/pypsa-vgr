import streamlit as st
from map_selector import custom_map_selector

result = custom_map_selector(
    default=["1480"],
)
st.write("Selection in map: %s" % result)
