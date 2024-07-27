import os.path
import atlite
import yaml
import pathlib
from atlite.gis import ExclusionContainer

def availability_matrix(cutout, selection, type, root_data = "../data", country_code = "SWE"):
    # Exclude land use per solar/wind

    if country_code == "SWE":
    
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
        
        CORINE = f"{root_data}/geo/corine.tif"

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
    else:
        # Source: https://egis.environment.gov.za/sa_national_land_cover_datasets
        # Download "South African National Land Cover (SANLC), 2022" Level 1 and 2 with info
        # Download tif: https://egis.environment.gov.za/data_egis/data_download/current

        # Level 1
        # 1 Forest Land
        # 2 Shrubland
        # 3 Grassland
        # 4 Waterbodies
        # 5 Wetlands
        # 6 Barren land
        # 7 Cultivated
        # 8 Built-up
        # 9 Mines and quarries

        # Level 2
        # 1 Natural wooded land
        # 2 Planted forest
        # 3 Shrubs
        # 4 Karoo and fynbos shrubland
        # 5 Natural grassland
        # 6 Natural
        # 7 Artificial
        # 8 Herbaceous wetlands
        # 9 Woody wetlands
        # 10 Consolidated
        # 11 Unconsolidated
        # 12 Permanent crops
        # 13 Temporal crops
        # 14 Fallow land and old fields
        # 15 Residential
        # 16 Village 
        # 17 Small holdings / Pre-urban SPLUMA
        # 18 Urban vegetation
        # 19 Commercial
        # 20 Industrial
        # 21 Transport
        # 22 Surface infrastructure
        # 23 Extraction sites
        # 24 Mine waste and resource dumps

        # Land-cover classes NOT included for solar areas:
        EXCLUDED_SOLAR = [1, 2, 4, 5, 7, 8, 9]
        # Land-cover classes NOT included for wind energy areas:
        EXCLUDED_WIND_NON_OCEAN = [1, 4, 5, 8]
        INCLUDED_WIND_OCEAN = [4] 

        CORINE = f"{root_data}/geo/sanlc.tif"

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

        excluder.add_raster(CORINE, codes=exclusion[type]['codes'], invert=exclusion[type]['invert'], crs="EPSG:4326")

        return cutout.availabilitymatrix(selection, excluder)


def capacity_factor(cutout, selection, type, model, root_data = "../data", country_code = "SWE"):

    base_dir = pathlib.Path(__file__).parent.parent
    wind_turbine = base_dir / 'library' / 'windturbine' / model

    avail = availability_matrix(cutout, selection, type, root_data, country_code)
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