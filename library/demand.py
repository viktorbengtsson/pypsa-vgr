import pandas as pd
import math
import paths

def normalize_demand():
    # This script takes the timvärden output from Svenska Kraftnät statistics (currently for 2023) and creates a normalized data for SE3 (elområde/electricity area)
    # The file is part of the repo so only need to run this file if the downloaded statistics changes

    ## Load the data, use only the timestamp column and the total consumption for SE3 (in column 4) and skip the first 5 rows that consist of header data. Create a new header.
    timvarden = pd.read_csv(paths.input_path / 'demand/timvarden-2023-01-12.csv', delimiter=',', skiprows=5, usecols=[0,3], header=None)
    timvarden.columns = ['timestamp', 'se3']

    ## Create an index from the timestamp column. Convert the se3 column to float, remove the thousand separator and change the sign to positive.
    timvarden['timestamp'] = pd.to_datetime(timvarden['timestamp'], format='%d.%m.%Y %H:%M')
    timvarden.set_index('timestamp', inplace=True)
    timvarden['se3'] = -timvarden['se3'].str.replace(',', '').astype(float)

    ## Resample the hourly data to 3h data selecting the max value in each 3h period
    tretimvarden = timvarden.resample('3h').max()

    ## Normalize the load so that total production for the year is 1MWh
    normalized_load = tretimvarden / (tretimvarden.sum() * 3)

    ## Save to file
    normalized_load.to_csv(paths.input_path / 'demand/normalized-load-2023-3h.csv')

# This calculation is based on a 2023 estimate from energiforetagen.se that can be fetched here: https://www.energiforetagen.se/pressrum/pressmeddelanden/2023/ny-rapport-sa-moter-vi-sveriges-elbehov-2045/
# It projectes an increase from 140 TWh annually in 2023 to 330 TWh annually in 2045
ENERGY_DEMAND_GROWTH = math.exp(math.log(330/140)/(2045-2023)) - 1

# Caluclate projected energy in MWh annually
# The parameter self_sufficiency ranges from 0 to 2 where the first 0 to 1 denotes fraction of new demand (on top of base demand) and 
def projected_energy(target_year, self_sufficiency):
    base_year = 2023
    base_demand = 19 # TWh per year
    fraction_new = min(self_sufficiency, 1)
    fraction_base = max(0, self_sufficiency - 1)

    return fraction_new * ( base_demand * (1 + ENERGY_DEMAND_GROWTH) ** (target_year - base_year) - base_demand ) + fraction_base * base_demand