import pandas as pd
import geopandas as gpd
import atlite
from shapely.ops import unary_union
from shapely.geometry import Polygon

def generate_cutout(lan_code, kom_code, weather_start, weather_end, root_data_path = "../data", country_code = "SWE"):
    if country_code == "SWE":
        #Source Lantmäteriverket, data maintained by opendatasoft.com
        country = gpd.read_file(f"{root_data_path}/geo/georef-sweden-kommun@public.geojson")
        
        lan = country.loc[country['lan_code'].isin([lan_code])]
    else:
        #Source: https://www.igismap.com/south-africa-shapefile-download-boundary-line-polygon/
        country = gpd.read_file(f"{root_data_path}/geo/south_africa_Province_level_1.geojson")
        
        lan = country.loc[country['shapeiso'].isin([lan_code])]
            
    minx, miny, maxx, maxy = lan.total_bounds

    fname = str(f"{root_data_path}/cutout-{lan_code}-{weather_start}-{weather_end}.nc")
    
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

    eez = None
    if country_code == "SWE":
        if kom_code is None:
            selection = gpd.GeoDataFrame(geometry=[unary_union(lan.geometry)], crs=country.crs)
        else:
            kom = country.loc[country['kom_code'].isin([kom_code])]
            selection = gpd.GeoDataFrame(geometry=[unary_union(kom.geometry)], crs=country.crs)

        # EEZ (Economical zone)
        shapefile_path = f"{root_data_path}/geo/Ekonomiska_zonens_yttre_avgränsningslinjer/Ekonomiska_zonens_yttre_avgränsningslinjer_linje.shp"
        eez_shape = gpd.read_file(shapefile_path).to_crs(selection.crs)
        min_x, min_y, max_x, max_y = eez_shape.total_bounds
        # Arbitrarily using min/max from cutout or eez to visualize it on VGR region
        bounding_box = Polygon([(min_x, miny), (min_x, maxy), (maxx, maxy), (maxx, miny)])
        bounds = gpd.GeoDataFrame(geometry=[bounding_box], crs=selection.crs) 
        eez = gpd.overlay(eez_shape, bounds, how='intersection')
        eez.to_crs(selection.crs)
    else:
        selection = gpd.GeoDataFrame(geometry=[unary_union(lan.geometry)], crs=country.crs)

    index = pd.to_datetime(cutout.coords['time'])

    return [cutout, selection, eez, index]
