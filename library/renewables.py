import atlite
from atlite.gis import ExclusionContainer
import paths
import xarray as xr

renewables_path = paths.input_path / 'renewables'

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
    
    CORINE = paths.input_path / 'geo/corine.tif'

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

def capacity_factor(cutout, selection, energy_type, generator, weather_geo, section_geo, weather_start, weather_end):

    section_key = None if section_geo is None else (section_geo if not isinstance(section_geo, list) else "-".join(section_geo))
    geo_key = f"{weather_geo}-{section_key}" if section_key is not None else weather_geo

    wind_turbine = renewables_path / 'windturbine' / generator
    matrix_path = renewables_path / f"availability-matrix-{geo_key}-{weather_start}-{weather_end}-{energy_type}.nc"

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

def store_availability_matrix(cutout, selection, energy_type, weather_geo, section_geo, weather_start, weather_end):

    section_key = None if section_geo is None else (section_geo if not isinstance(section_geo, list) else "-".join(section_geo))
    geo_key = f"{weather_geo}-{section_key}" if section_key is not None else weather_geo

    matrix_path = renewables_path / f"availability-matrix-{geo_key}-{weather_start}-{weather_end}-{energy_type}.nc"

    if not matrix_path.is_file():
        avail_matrix = availability_matrix(cutout, selection, energy_type)
        avail_matrix.to_netcdf(matrix_path)

def store_capacity_factor(cutout, selection, energy_type, model, weather_geo, section_geo, weather_start, weather_end):

    section_key = None if section_geo is None else (section_geo if not isinstance(section_geo, list) else "-".join(section_geo))
    geo_key = f"{weather_geo}-{section_key}" if section_key is not None else weather_geo

    capfac_path = renewables_path / f"capacity-factor-{geo_key}-{weather_start}-{weather_end}-{energy_type}.nc"

    if not capfac_path.is_file():
        capfac = capacity_factor(cutout, selection, energy_type, model, weather_geo, section_geo, weather_start, weather_end)
        capfac.to_netcdf(capfac_path)