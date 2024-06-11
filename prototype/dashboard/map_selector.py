import numpy as np
import pandas as pd
import time
import streamlit as st
import matplotlib.pyplot as plt
import folium
from shapely.geometry import Point
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import geopandas as gpd
from shapely.ops import unary_union

########## / Functions etc \ ##########

# Function to determine if a point is inside a polygon
def point_in_polygon(point, poly):
    return poly.contains(Point(point))

def reset_geo(**kwargs):
    if "clear_kom_only" in kwargs and kwargs["clear_kom_only"]:
        st.query_params.geography = kwargs["lan_code"]
    else:
        st.query_params.geography = None

########## \ Functions / ##########

def render_map(selected_lan_code, selected_kom_code):
    ########## / Collection of data \ ##########

    # Select region, then municipal (start with Sweden)
    sweden = gpd.read_file(f"../../data/geo/georef-sweden-kommun@public.geojson") #Source Lantmäteriverket, data maintained by opendatasoft.com

    selection = sweden
    if selected_lan_code is not None:
        lan = sweden.loc[sweden.lan_code.apply(lambda x: selected_lan_code in x)]
    if selected_kom_code is not None:
        if selected_lan_code is None:
            raise Exception("selected_lan is required together with selected_kom")

        #selection = sweden.loc[sweden.kom_code.apply(lambda x: selected_kom_code in x)]
        selection = lan
    elif selected_lan_code is not None:
        selection = lan

    min_x, min_y, max_x, max_y = selection.total_bounds

    # Add regions to the map (for selecting region)
    selection_polygons = {}
    if selected_lan_code is None:
        code_column = "lan_code"
        name_column = "lan_name"
    elif selected_kom_code is None:
        code_column = "kom_code"
        name_column = "kom_name"
    else:
        code_column = "kom_code"
        name_column = "kom_name"

    for index, row in selection.iterrows():
        if row.geometry.geom_type == 'Polygon':
            if row[code_column][0] in selection_polygons:
                selection_polygons[row[code_column][0]][0].append(row.geometry)
            else:
                selection_polygons[row[code_column][0]] = ([row.geometry], row[name_column][0], row["lan_code"][0], row["lan_name"][0], row["kom_code"][0], row["kom_name"][0])
        elif row.geometry.geom_type == 'MultiPolygon':
            if not row[code_column][0] in selection_polygons:
                selection_polygons[row[code_column][0]] = ([], row[name_column][0], row["lan_code"][0], row["lan_name"][0], row["kom_code"][0], row["kom_name"][0])
            for poly_idx, polygon in enumerate(row.geometry.geoms):
                selection_polygons[row[code_column][0]][0].append(polygon)

    # Merge all polygons (union)
    selected_lan_name = None
    selected_kom_name = None
    area_polygons = {}
    for code, item in selection_polygons.items():
        geo = unary_union(item[0])

        if geo.geom_type == 'Polygon':
            polygons = [geo]
        elif geo.geom_type == 'MultiPolygon':
            polygons = []
            for poly_idx, polygon in enumerate(geo.geoms):
                polygons.append(polygon)

        area_polygons[code] = (polygons, item[1], item[2], item[3])
        if selected_lan_code:
            selected_lan_name = item[3]
        if selected_kom_code:
            selected_lan_name = item[3]
            if selected_kom_code == item[4]:
                selected_kom_name = item[5]

    ########## \ Collection of data / ##########

    m = folium.Map(location=[(min_y+max_y)/2,(min_x+max_x)/2], zoom_start=5, tiles="cartodb positron")
    m.fit_bounds([[min_y,min_x],[max_y,max_x]])

    color = "#000000"
    for code, item in area_polygons.items():
        fillColor = "#228822"
        if selected_lan_code == code:
            color = "#228822"
        if selected_kom_code == code:
            fillColor = "yellow"

        for polygon in item[0]:
            folium.Polygon(locations=[(y, x) for x, y in polygon.exterior.coords], color=color, weight=0.25, fillColor=fillColor, tooltip=f"<div style=\"font-size: 1.5rem;\">{item[1]}</div>").add_to(m)

    #selected_year = st.sidebar.number_input("Year", min_value=2010, max_value=2050, value=2011)

    height = streamlit_js_eval(js_expressions='screen.height', key = 'SCR')
    if height is None:
        height = 800
    side_col1, side_col2 = st.sidebar.columns([1, 1])
    if selected_kom_code is not None:
        side_col1.button(f":x: {selected_lan_name}", on_click=reset_geo, kwargs={ "clear_kom_only": False, "lan_code": selected_lan_code }, use_container_width=True)
        side_col2.button(f":x: {selected_kom_name}", on_click=reset_geo, kwargs={ "clear_kom_only": True, "lan_code": selected_lan_code }, use_container_width=True)
    elif selected_lan_code is not None:
        side_col1.button(f":x: {selected_lan_name}", on_click=reset_geo, kwargs={ "clear_kom_only": False, "lan_code": selected_lan_code }, use_container_width=True)


    # This is the command that causes multiple renders
    map_output = st_folium(m, width="100%", height=height)
    #st.sidebar.write("ToDo: Use maps without the ocean in clickable areas")


    # Inject custom CSS to set the width of the sidebar
    st.markdown(
        f"""
        <style>
            section[data-testid="stSidebar"] {{
                width: 450px !important;
            }}
            div[data-testid="stSidebarUserContent"] {{
                padding-top: 3em;
            }}
            section[data-testid="stSidebar"] div.stHeadingContainer h1 {{
                padding-top: 0;
                padding-bottom: 0.5em;
            }}
            div[data-testid="stSidebarUserContent"] iframe {{
                position: fixed;
                top: 2px;
                left: 0;
                width: 450px;
                height: {height-2}px;
                z-index: 10;
            }}
            div[data-testid="stSidebarUserContent"] > div div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {{
                position: absolute;
                margin-top: -3em;
                zoom: 0.8;
                z-index: 20;
                margin-left: 2.5em;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if map_output and map_output['last_clicked']:
        clicked_point = map_output['last_clicked']

        # Check which area was clicked
        selected_kom_code = None
        for code, item in area_polygons.items():
            for polygon in item[0]:
                if point_in_polygon((clicked_point['lng'], clicked_point['lat']), polygon):
                    if selected_lan_code is not None:
                        st.query_params.geography = f"{selected_lan_code}:{code}"
                    else:
                        st.query_params.geography = code

                    time.sleep(0.1) # Bug: https://github.com/streamlit/streamlit/issues/5511
                    st.rerun()
                    break
