import pandas as pd
#import geopandas as gpd
#import atlite
#import csv
#import shutil
#import xarray as xr
#from shapely.ops import unary_union
#from shapely.geometry import Polygon
#from atlite.gis import ExclusionContainer
#import pypsa

def create_and_store_demand(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    YEAR=scenario_config["demand"]
    TARGET=scenario_config["demand-target"]
    INDEX = pd.to_datetime(pd.read_csv(f"../{DATA_PATH}/time_index.csv")["0"])

    # Calculate demand (source: 2025 from behovskartan.se)

    ## Load the demand data (it comes in a format of peak demand per each hour and per month and per weekend/weekday and per h3 hexagon)
    demand_data = pd.read_csv(f'../data/demand/demand_vgr_{YEAR}.csv')
    demand_year = demand_data['Year'][0]
    demand_data.drop(columns=['Unnamed: 0', 'Year'], inplace=True)
    demand_data['Timestamp'] = pd.to_datetime(demand_data['Timestamp'], format='%Y-%m-%d %H:%M:%S')
    demand_data.set_index('Timestamp', inplace=True)
    
    ## Aggregate by summing over all the hexagons and resampling from 1h to 3h intervals
    grouped_demand_data = demand_data.groupby([demand_data.index, 'Daytype']).sum()['Demand (MW)'].groupby([pd.Grouper(freq='3h', level=0), 'Daytype']).mean()
    
    ## Function that returns the approlpriate demand for a given day
    def select_demand(index):
        groupd_idx = (index.replace(year=demand_year ,day=1),'weekday' if index.weekday() < 5 else 'weekend')
        return grouped_demand_data[groupd_idx]
    
    ## Build a load profile
    demand_total = [select_demand(i) for i in INDEX]
    demand_target = [TARGET*p for p in demand_total]
    demand = pd.DataFrame({'time': INDEX, 'total': demand_total, 'target': demand_target})
    demand.set_index('time', inplace=True)
    demand.to_csv(f"../{DATA_PATH}/demand.csv")

