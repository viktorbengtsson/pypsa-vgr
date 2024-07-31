import os.path
import sys
import pandas as pd
import geopandas as gpd
import atlite
from shapely.ops import unary_union
from shapely.geometry import Polygon

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

def generate_cutout(lan_code, kom_code, weather_start, weather_end):
    #Source Lantmäteriverket, data maintained by opendatasoft.com
    sweden = gpd.read_file("data/geo/georef-sweden-kommun@public.geojson")
    # Remove useless arrays
    sweden.loc[:, "lan_code"] = sweden.lan_code.apply(lambda x : x[0])
    sweden.loc[:, "kom_code"] = sweden.kom_code.apply(lambda x : x[0])
    sweden.loc[:, "lan_name"] = sweden.lan_name.apply(lambda x : x[0])
    sweden.loc[:, "kom_name"] = sweden.kom_name.apply(lambda x : x[0])
    
    lan = sweden.loc[sweden['lan_code'].isin([lan_code])]
    
    minx, miny, maxx, maxy = lan.total_bounds

    fname = str(f"data/cutout-{lan_code}-{weather_start}-{weather_end}.nc")
    
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

    if kom_code is None:
        selection = gpd.GeoDataFrame(geometry=[unary_union(lan.geometry)], crs=sweden.crs)
    else:
        kom = sweden.loc[sweden['kom_code'].isin([kom_code])]
        selection = gpd.GeoDataFrame(geometry=[unary_union(kom.geometry)], crs=sweden.crs)
    
    # EEZ (Economical zone)
    shapefile_path = "data/geo/Ekonomiska_zonens_yttre_avgränsningslinjer/Ekonomiska_zonens_yttre_avgränsningslinjer_linje.shp"
    eez_shape = gpd.read_file(shapefile_path).to_crs(selection.crs)
    min_x, min_y, max_x, max_y = eez_shape.total_bounds
    # Arbitrarily using min/max from cutout or eez to visualize it on VGR region
    bounding_box = Polygon([(min_x, miny), (min_x, maxy), (maxx, maxy), (maxx, miny)])
    bounds = gpd.GeoDataFrame(geometry=[bounding_box], crs=selection.crs) 
    eez = gpd.overlay(eez_shape, bounds, how='intersection')
    eez.to_crs(selection.crs)

    index = pd.to_datetime(cutout.coords['time'])

    return [cutout, selection, eez, index]