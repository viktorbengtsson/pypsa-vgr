import pandas as pd
import geopandas as gpd
import atlite
from shapely.ops import unary_union
from shapely.geometry import Polygon

from input.geo.geo_core import get_geo
import paths

def generate_cutout(lan_code, sections, weather_start, weather_end):
    
    #Source Lantmäteriverket, data maintained by opendatasoft.com
    geo_area = gpd.read_file(paths.input_root / 'geo/georef-sweden-kommun@public.geojson')
    
    main_area = geo_area.loc[geo_area['lan_code'].isin([lan_code])]
    
    minx, miny, maxx, maxy = main_area.total_bounds

    fname = paths.weather /  f"cutout,geography={lan_code},start={weather_start},end={weather_end}.nc"
    
    cutout = atlite.Cutout(
        path=fname,
        module="era5",
        x=slice(minx, maxx),
        y=slice(miny, maxy),
        time=slice(weather_start,weather_end),
        dx=0.125,
        dy=0.125,
        dt="3h"
    )

    cutout.prepare(features=['influx', 'temperature', 'wind'])

    selections = {
        lan_code: gpd.GeoDataFrame(geometry=[unary_union(main_area.geometry)], crs=geo_area.crs)
    }

    if sections is not None:
        for _, item in sections.items():
            if isinstance(item, list):
                kom = geo_area.loc[geo_area['kom_code'].isin(item)]
                selections[f"{'-'.join(item)}"] = gpd.GeoDataFrame(geometry=[unary_union(kom.geometry)], crs=geo_area.crs)
            else:
                kom = geo_area.loc[geo_area['kom_code'].isin([item])]
                selections[item] = gpd.GeoDataFrame(geometry=[unary_union(kom.geometry)], crs=geo_area.crs)

    # EEZ (Economical zone)
    shapefile_path = paths.input_root / 'geo/Ekonomiska_zonens_yttre_avgränsningslinjer/Ekonomiska_zonens_yttre_avgränsningslinjer_linje.shp'
    eez_shape = gpd.read_file(shapefile_path).to_crs(geo_area.crs)
    min_x, min_y, max_x, max_y = eez_shape.total_bounds
    # Arbitrarily using min/max from cutout or eez to visualize it on VGR region
    bounding_box = Polygon([(min_x, miny), (min_x, maxy), (maxx, maxy), (maxx, miny)])
    bounds = gpd.GeoDataFrame(geometry=[bounding_box], crs=geo_area.crs) 
    eez = gpd.overlay(eez_shape, bounds, how='intersection')
    eez.to_crs(geo_area.crs)

    index = pd.to_datetime(cutout.coords['time'])

    return [cutout, selections, eez, index]

def store_weather(geo, sections, weather_start, weather_end):
    cutout_path = paths.weather / f"cutout,geography={geo},start={weather_start},end={weather_end}.nc"
    index_path = paths.weather / f"index,geography={geo},start={weather_start},end={weather_end}.nc"

    cutout, selections, eez, index = generate_cutout(geo, sections, weather_start, weather_end)

    index.to_series().to_csv(index_path)

    for key, selection in selections.items():
        selection_path = paths.weather / f"selection,geography={key},start={weather_start},end={weather_end}.shp"

        if not selection_path.is_file():
            selection.to_file(selection_path)

def load_weather(geo, section, weather_start, weather_end):
    cutout_path = paths.weather / f"cutout,geography={geo},start={weather_start},end={weather_end}.nc"

    section_key = None if section is None else (section if not isinstance(section, list) else "-".join(section))
    geo_key = section_key if section_key is not None else geo

    selection_path = paths.weather / f"selection,geography={geo_key},start={weather_start},end={weather_end}.shp"

    cutout = atlite.Cutout(cutout_path)
    selection = gpd.read_file(selection_path)
    index = pd.to_datetime(cutout.coords['time'])

    return cutout, selection, index
