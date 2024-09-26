import streamlit as st
import itertools
from library.config import set_data_root, read_dashboard_available_variables

# Provide the map with the selectable geographic sections
# Selectbox normally not visible (since we're running single main_geo). So just for testing
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
        main_geo = next(iter(sections))
    else:
        main_geo = st.selectbox("",
            sections.keys(),
            label_visibility="collapsed",
            index=list(sections.keys()).index(current_main_geo)
        )

    # Get the "selectable" items from the config geo "keys". They can be "14", "14:1480" (where we want the "1480" part), or like "14:1480-1481-1482..." where we want each individual value 1480,1481, 1482 etc
    section_values = list(itertools.chain.from_iterable(sections.values()))
    #section_values = [s for s in section_values if len(s) > 4]
    #section_values = [section_values[3:] if len(section_values) > 4 else "3" for section_values in section_values]
    #print(section_values)

    #available_geo = list(filter(lambda a: a[:2] == main_geo, list(sections.keys()) + section_values))

    available_geo = []

    for value in section_values:
        if len(value) > 4:
            available_geo.extend(value.split('-'))
        else:
            available_geo.append(value)

    return section_values, main_geo