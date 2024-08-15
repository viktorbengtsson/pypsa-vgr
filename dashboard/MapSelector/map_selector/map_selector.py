import os

import streamlit.components.v1 as components


# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = True

if not _RELEASE:
    _map_selector = components.declare_component(
        "map_selector",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _map_selector = components.declare_component("map_selector", path=build_dir)


def streamlit_map_selector(main_geo, initial_geo, available_geo, country="sweden", key=None):
    return _map_selector(main_geo=main_geo, initial_geo=initial_geo, available_geo=available_geo, country=country, key=key)
