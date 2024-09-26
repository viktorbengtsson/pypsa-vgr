import atlite
from atlite.gis import ExclusionContainer
import paths
import xarray as xr
import numpy as np


def excluder(energy_type):
    # Exclude land use per solar/wind
    
    # Source: https://www.uts.edu.au/oecm/renewable-resource-mapping
    # (Classification mapping: https://collections.sentinel-hub.com/corine-land-cover/readme.html)
    # With the exception of "41; Water bodies"
    
    # Land-cover classes NOT included for solar areas:
    # 1.1.1,1.2.2,1.2.3,1.2.4,1.3.1,1.3.3,1.4.1,1.4.2,3.1.1,3.1.2,3.1.3,3.2.2,3.3.1,3.3.4,3.3.5,4.1.1,4.1.2,4.2.1,4.2.2,4.2.3,5.1.1,5.1.2,5.2.1,5.2.2,5.2.3
    EXCLUDED_SOLAR = [1,4,5,6,7,9,10,11,23,24,25,27,30,33,34,35,36,37,38,39,40,41,42,43,44]
    
    # Land-cover classes NOT included for wind energy areas:
    # 1.1.1,1.1.2,1.2.1,1.2.2,1.2.3,1.2.4,1.3.1,1.3.3,1.4.1,1.4.2,2.2.1,2.2.2,2.2.3,3.1.1,3.1.2,3.1.3,3.2.2,3.3.1,3.3.2,3.3.4,3.3.5,4.1.1,4.1.2,4.2.1,4.2.2,4.2.3,5.1.1,5.1.2,5.2.1,5.2.2,5.2.3
    EXCLUDED_WIND_NON_OCEAN = [1,2,3,4,5,6,7,9,10,11,15,16,17,23,24,25,27,30,31,33,34,35,36,37,38,39,40,41,42,43,44]
    # 5.2.3, 5.1.2
    INCLUDED_WIND_OCEAN = [44, 41]
    
    CORINE = paths.input_root / 'geo/corine.tif'

    exclusion = {
        'solar': {
            'codes': EXCLUDED_SOLAR,
            'invert': False
        },
        'onwind': {
            'codes': EXCLUDED_WIND_NON_OCEAN,
            'invert': False
        },
        'offwind': {
            'codes': INCLUDED_WIND_OCEAN,
            'invert': True
        }
    }

    exclcont = ExclusionContainer()

    exclcont.add_raster(CORINE, codes=exclusion[energy_type]['codes'], invert=exclusion[energy_type]['invert'])

    return exclcont

def availability_matrix(cutout, selection, energy_type):
    type_excluder = excluder(energy_type)
    return cutout.availabilitymatrix(selection, type_excluder)

def capacity_factor(cutout, selection, energy_type, generator, weather_geo, section, weather_start, weather_end):

    geo = section if section is not None else weather_geo

    wind_turbine = paths.renewables_root / 'windturbines_core' / generator
    matrix_path = paths.renewables / f"availability-matrix-{energy_type},geography={geo},start={weather_start},end={weather_end}.nc"

    if (matrix_path).is_file():
        avail = xr.open_dataarray(matrix_path)
    else:
        avail = availability_matrix(cutout, selection, energy_type)

    avail_matrix = avail.stack(spatial=["y", "x"])

    match energy_type:
        case 'solar':
            return cutout.pv(
                matrix=avail_matrix,
                panel=atlite.solarpanels.CdTe,
                orientation="latitude_optimal",
                index=selection.index,
                per_unit =True,
            )
        case 'onwind':
            return cutout.wind(
                matrix=avail_matrix,
                turbine = atlite.resource.get_windturbineconfig(wind_turbine),
                index=selection.index,
                per_unit =True,
            )

        case 'offwind':
            return cutout.wind(
                matrix=avail_matrix,
                turbine = atlite.resource.get_windturbineconfig(wind_turbine),
                index=selection.index,
                per_unit =True,
            )
        case _:
            print("Unknown energy type (solar, onwind, offwind)")
            return

def store_availability_matrix(cutout, selection, energy_type, weather_geo, section, weather_start, weather_end):

    geo = section if section is not None else weather_geo
    matrix_path = paths.renewables / f"availability-matrix-{energy_type},geography={geo},start={weather_start},end={weather_end}.nc"

    if not matrix_path.is_file():
        avail_matrix = availability_matrix(cutout, selection, energy_type)
        avail_matrix.to_netcdf(matrix_path)

def store_capacity_factor(cutout, selection, energy_type, model, weather_geo, section, weather_start, weather_end):

    geo = section if section is not None else weather_geo
    capfac_path = paths.renewables / f"capacity-factor-{energy_type},geography={geo},start={weather_start},end={weather_end}.nc"

    if not capfac_path.is_file():
        capfac = capacity_factor(cutout, selection, energy_type, model, weather_geo, section, weather_start, weather_end)
        capfac.to_netcdf(capfac_path)