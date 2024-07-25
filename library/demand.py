import pandas as pd

# This script takes the timvärden output from Svenska Kraftnät statistics (currently for 2023) and creates a normalized data for SE3 (elområde/electricity area)
# The file is part of the repo so only need to run this file if the downloaded statistics changes

## Load the data, use only the timestamp column and the total consumption for SE3 (in column 4) and skip the first 5 rows that consist of header data. Create a new header.
timvarden = pd.read_csv(f"../data/demand/timvarden-2023-01-12.csv", delimiter=',', skiprows=5, usecols=[0,3], header=None)
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
normalized_load.to_csv(f"../data/demand/normalized-load-2023-3h.csv")
