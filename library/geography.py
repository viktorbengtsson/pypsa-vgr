import atlite
from atlite.gis import ExclusionContainer
import paths

def availability_matrix(cutout, selection, type):
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

    excluder = ExclusionContainer()

    excluder.add_raster(CORINE, codes=exclusion[type]['codes'], invert=exclusion[type]['invert'])

    return cutout.availabilitymatrix(selection, excluder)

def capacity_factor(cutout, selection, type, model):

    wind_turbine = paths.library_path / 'windturbine' / model

    avail = availability_matrix(cutout, selection, type)
    avail_matrix = avail.stack(spatial=["y", "x"])

    match type:
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