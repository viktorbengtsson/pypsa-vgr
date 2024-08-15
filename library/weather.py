import pandas as pd
import geopandas as gpd
import atlite
from shapely.ops import unary_union
from shapely.geometry import Polygon
import paths

weather_path = paths.input_path / 'weather'

def generate_cutout(lan_code, sections, weather_start, weather_end):
    
    #Source Lantmäteriverket, data maintained by opendatasoft.com
    geo_area = gpd.read_file(paths.input_path / 'geo/georef-sweden-kommun@public.geojson')
    
    main_area = geo_area.loc[geo_area['lan_code'].isin([lan_code])]
    
    minx, miny, maxx, maxy = main_area.total_bounds

    fname = weather_path /  f"cutout-{lan_code}-{weather_start}-{weather_end}.nc"
    
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

    for _, item in sections.items():
        if isinstance(item, list):
            kom = geo_area.loc[geo_area['kom_code'].isin(item)]
            selections[f"{lan_code}:{':'.join(item)}"] = gpd.GeoDataFrame(geometry=[unary_union(kom.geometry)], crs=geo_area.crs)
        else:
            kom = geo_area.loc[geo_area['kom_code'].isin([item])]
            selections[f"{lan_code}:{item}"] = gpd.GeoDataFrame(geometry=[unary_union(kom.geometry)], crs=geo_area.crs)

    # EEZ (Economical zone)
    shapefile_path = paths.input_path / 'geo/Ekonomiska_zonens_yttre_avgränsningslinjer/Ekonomiska_zonens_yttre_avgränsningslinjer_linje.shp'
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
    cutout_path = weather_path / f"cutout-{geo}-{weather_start}-{weather_end}.nc"
    index_path = weather_path / f"index-{geo}-{weather_start}-{weather_end}.csv"

    cutout, selections, eez, index = generate_cutout(geo, sections, weather_start, weather_end)

    index.to_series().to_csv(index_path)

    for key, selection in selections.items():
        file_key = key.replace(":", "-")
        selection_path = weather_path / f"selection-{file_key}-{weather_start}-{weather_end}.shp"

        if not selection_path.is_file():
            selection.to_file(selection_path)

def load_weather(weather_geo, section_geo, weather_start, weather_end):
    cutout_path = weather_path / f"cutout-{weather_geo}-{weather_start}-{weather_end}.nc"

    section_key = None if section_geo is None else (section_geo if not isinstance(section_geo, list) else "-".join(section_geo))
    geo_key = f"{weather_geo}-{section_key}" if section_key is not None else weather_geo

    selection_path = weather_path / f"selection-{geo_key}-{weather_start}-{weather_end}.shp"

    cutout = atlite.Cutout(cutout_path)
    selection = gpd.read_file(selection_path)

    return cutout, selection
