import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
import os.path
from gen_table import render_generators_table
from capacity_chart import render_capacity_chart
from energy_chart import render_energy_chart
from lab import render_network, render_demand


########## / Functions etc \ ##########

ROOT = ".."

# Function to determine if a point is inside a polygon
def point_in_polygon(point, poly):
    return poly.contains(Point(point))

def reset_geo(**kwargs):
    if "clear_kom_only" in kwargs and kwargs["clear_kom_only"]:
        st.session_state.kom = None
        st.query_params.kom = None
    else:
        st.session_state.lan = None
        st.session_state.kom = None
        st.query_params.lan = None
        st.query_params.kom = None


########## \ Functions / ##########


########## / Streamlit init \ ##########

st.set_page_config(layout="wide")
st.title('PyPSA-VGR')
col1, col2 = st.columns([2, 1])

st.markdown(
    """
    <style>
        div[class^='block-container'] {
            padding-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

########## \ Streamlit init / ##########

########## / State \ ##########
if 'lan' not in st.session_state:
    st.session_state['lan'] = None
if 'kom' not in st.session_state:
    st.session_state['kom'] = None
if 'lan' not in st.query_params:
    st.query_params.lan = None
if 'kom' not in st.query_params:
    st.query_params.kom = None

selected_lan_code = st.query_params.lan
selected_kom_code = st.query_params.kom

if st.session_state.lan is None:
    selected_lan_code = None if st.query_params.lan == "None" else st.query_params.lan
else:
    selected_lan_code = st.session_state.lan
    st.query_params.lan = selected_lan_code

if st.session_state.kom is None:
    selected_kom_code = None if st.query_params.kom == "None" else st.query_params.kom
else:
    selected_kom_code = st.session_state.kom
    st.query_params.kom = selected_kom_code


########## \ State / ##########

########## / Collection of data \ ##########

# Select region, then municipal (start with Sweden)
sweden = gpd.read_file(f"{ROOT}/data/geo/georef-sweden-kommun@public.geojson") #Source Lantmäteriverket, data maintained by opendatasoft.com

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

########## / Folium map \ ##########

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
        folium.Polygon(locations=[(y, x) for x, y in polygon.exterior.coords], color=color, weight=1, fillColor=fillColor, tooltip=f"<div style=\"font-size: 1.5rem;\">{item[1]}</div>").add_to(m)

#selected_year = st.sidebar.number_input("Year", min_value=2010, max_value=2050, value=2011)

height = 800 if selected_lan_code is None else 400
side_col1, side_col2 = st.sidebar.columns([1, 1])
if selected_kom_code is not None:
    side_col1.button(f":x: {selected_lan_name}", on_click=reset_geo, kwargs={ "clear_kom_only": False }, use_container_width=True)
    side_col2.button(f":x: {selected_kom_name}", on_click=reset_geo, kwargs={ "clear_kom_only": True }, use_container_width=True)
elif selected_lan_code is not None:
    side_col1.button(f":x: {selected_lan_name}", on_click=reset_geo, kwargs={ "clear_kom_only": False }, use_container_width=True)
else:
    st.sidebar.title(f"Select a region")

with st.sidebar:
    map_output = st_folium(m, width=400, height=height)
    print("MAPPING")
    #st.sidebar.write("ToDo: Too many roundtrips per click on map")
    #st.sidebar.write("ToDo: Use maps without the ocean in clickable areas")


# Inject custom CSS to set the width of the sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 450px !important;
        }
        div[data-testid="stSidebarUserContent"] {
            padding-top: 3em;
        }
        section[data-testid="stSidebar"] div.stHeadingContainer h1 {
            padding-top: 0;
            padding-bottom: 0.5em;
        }
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
                    st.session_state.kom = code
                else:
                    st.session_state.lan = code

                st.rerun()
                break



########## \ Folium map / ##########



########## / Energy info from selection \ ##########

if selected_lan_code:
    selected_year = 2011
    START=f"{str(selected_year)}-01"
    END=f"{str(selected_year)}-12"

    filepattern = f"{ROOT}/data/result/{{}}-{selected_lan_code}-{selected_kom_code}-{START}-{END}.{{}}"

    testfile = filepattern.format("network", "nc")

    if not os.path.isfile(testfile):
        col1.write(f"No files for this selection, missing file: {testfile}")
    else:

        # Filters
        col2.slider("Konstruktion start och slut år", 2020, 2050, (2023, 2026))
        col2.checkbox("Begränsa turbiner?")
        col2.toggle("Vätgas på/av")
        col2.toggle("Biogas på/av")
        col2.slider("Min/max behov (MW)", 0.0, 100.0, (25.0, 75.0))

        render_generators_table(col1)
        col1.write("")
        col1.write("")
        col1.write("")
        render_capacity_chart(col1, col1)

        render_energy_chart(col2)

        #render_network(col2, filepattern)
        #render_demand(col1)

########## \ Energy info from selection / ##########

