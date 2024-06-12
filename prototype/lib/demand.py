import pandas as pd

def create_and_store_demand(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    YEAR=scenario_config["demand"]
    TARGET=scenario_config["load-target"]

    ## Load the data, use only the timestamp column and the total consumption for SE3 (in column 4) and skip the first 5 rows that consist of header data. Create a new header.
    timvarden = pd.read_csv(f"../data/demand/timvarden-{YEAR}-01-12.csv", delimiter=',', skiprows=5, usecols=[0,3], header=None)
    timvarden.columns = ['timestamp', 'se3']
    
    ## Create an index from the timestamp column. Convert the se3 column to float, remove the thousand separator and change the sign to positive.
    timvarden['timestamp'] = pd.to_datetime(timvarden['timestamp'], format='%d.%m.%Y %H:%M')
    timvarden.set_index('timestamp', inplace=True)
    timvarden['se3'] = -timvarden['se3'].str.replace(',', '').astype(float)
    
    ## Resample the hourly data to 3h data selecting the max value in each 3h period
    tretimvarden = timvarden.resample('3h').max()
    
    ## Normalize the load so that total production for the year is 1MWh
    normalized_load = tretimvarden / (tretimvarden.sum() * 3)
    
    ## VGR load is the normalized load pattern producing 19 TWh (19,000,000 MWh) per year
    demand = normalized_load * TARGET * 1_000_000
    demand.to_csv(f"../{DATA_PATH}/demand.csv")
