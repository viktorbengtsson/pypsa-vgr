import geopandas as gpd
import atlite
import pathlib
from atlite.gis import ExclusionContainer

def create_and_store_availability(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    WIND_TURBINE = config["onwind_turbine"]
    WIND_TURBINE_OFFSHORE = config["offwind_turbine"]
    CUTOUT = atlite.Cutout(f"../{DATA_PATH}/cutout.nc")
    SELECTION = gpd.read_file(f"../{DATA_PATH}/selection.shp")

    WIND_TURBINE = pathlib.Path(f"./lib/windturbine/{WIND_TURBINE}")
    WIND_TURBINE_OFFSHORE = pathlib.Path(f"./lib/windturbine/{WIND_TURBINE_OFFSHORE}")

    
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
    
    CORINE = "../data/geo/corine.tif"
    solar_excluder = ExclusionContainer()
    wind_onshore_excluder = ExclusionContainer()
    wind_offshore_excluder = ExclusionContainer()
    
    solar_excluder.add_raster(CORINE, codes=EXCLUDED_SOLAR)
    wind_onshore_excluder.add_raster(CORINE, codes=EXCLUDED_WIND_NON_OCEAN)
    wind_offshore_excluder.add_raster(CORINE, codes=INCLUDED_WIND_OCEAN, invert=True)

    solar_avail = CUTOUT.availabilitymatrix(SELECTION, solar_excluder)
    wind_onshore_avail = CUTOUT.availabilitymatrix(SELECTION, wind_onshore_excluder)
    wind_offshore_avail = CUTOUT.availabilitymatrix(SELECTION, wind_offshore_excluder)

    # Atlite availability results : SOLAR
    solar_availability_matrix = solar_avail.stack(spatial=["y", "x"])
    mean_solar_capacity_factor = CUTOUT.pv(
        matrix=solar_availability_matrix,
        panel=atlite.solarpanels.CdTe,
        orientation="latitude_optimal",
        index=SELECTION.index,
        per_unit =True,
    )
    # Atlite availability results : WIND ONSHORE
    wind_onshore_availability_matrix = wind_onshore_avail.stack(spatial=["y", "x"])
    mean_wind_onshore_capacity_factor = CUTOUT.wind(
        matrix=wind_onshore_availability_matrix,
        turbine = atlite.resource.get_windturbineconfig(WIND_TURBINE),
        index=SELECTION.index,
        per_unit =True,
    )
    # Atlite availability results : WIND OFFSHORE
    wind_offshore_availability_matrix = wind_offshore_avail.stack(spatial=["y", "x"])
    mean_wind_offshore_capacity_factor = CUTOUT.wind(
        matrix=wind_offshore_availability_matrix,
        turbine = atlite.resource.get_windturbineconfig(WIND_TURBINE_OFFSHORE),
        index=SELECTION.index,
        per_unit =True,
    )
    
    # Store the files
    solar_avail.to_netcdf(f"../{DATA_PATH}/avail_solar.nc")
    mean_solar_capacity_factor.to_netcdf(f"../{DATA_PATH}/avail_capacity_solar.nc")
    wind_onshore_avail.to_netcdf(f"../{DATA_PATH}/avail_onwind.nc")
    mean_wind_onshore_capacity_factor.to_netcdf(f"../{DATA_PATH}/avail_capacity_onwind.nc")
    wind_offshore_avail.to_netcdf(f"../{DATA_PATH}/avail_offwind.nc")
    mean_wind_offshore_capacity_factor.to_netcdf(f"../{DATA_PATH}/avail_capacity_offwind.nc")

