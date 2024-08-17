import streamlit as st
import itertools
from library.config import set_data_root, read_dashboard_available_variables

# Provide the map with the selectable geographic sections
def main_geo_selector(current_main_geo):
    # State management
    data_root = set_data_root()

    SCENARIOS = read_dashboard_available_variables(data_root)

    sections = {}
    for section in SCENARIOS["geography"]:
        main = section[:2]
        if main in sections:
            sections[main].append(section)
        else:
            sections[main] = [section]

    if (len(sections) == 1):
        main_geo = next(iter(sections.values()))[0]
    else:
        main_geo = st.selectbox("",
            sections.keys(),
            label_visibility="hidden",
            index=list(sections.keys()).index(current_main_geo)
        )

    available_geo = list(filter(lambda a: a[:2] == main_geo, list(sections.keys()) + list(itertools.chain.from_iterable(sections.values()))))

    return available_geo, main_geo