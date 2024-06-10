import numpy as np
import pandas as pd
import pypsa
import matplotlib.pyplot as plt
import netCDF4 as nc

def render_network(st_obj, config):
    DATA_PATH=config["scenario"]["data-path"]

    with nc.Dataset(f"../../{DATA_PATH}/network.nc", mode='r') as ds:
        st_obj.write("NetCDF file details:")
        st_obj.write(ds)

        # Display variables in the file
        st_obj.write("Variables in the file:")
        st_obj.write(ds.variables.keys())
        
        # Select a variable to display
        variable = st_obj.selectbox("Select a variable to visualize", list(ds.variables.keys()))
        
        # Fetch data for the selected variable
        data = ds.variables[variable][:]
        
        # Use matplotlib to plot the data
        plt.figure()
        plt.plot(data)
        plt.title(f'{variable} data')
        plt.xlabel('Index')
        plt.ylabel(variable)
        st_obj.pyplot(plt)

def render_demand(st_obj, config):
    # DEMAND
    #    demandfile = f"{ROOT}/data/result/demand-{selected_lan_code}-{selected_kom_code}-{START}-{END}.csv"
    #    indexfile = f"{ROOT}/data/result/index-{selected_lan_code}-{selected_kom_code}-{START}-{END}.csv"
    #    demand_data = pd.read_csv(demandfile)
    #    #demand_data.drop(columns=['Unnamed: 0', 'Year'], inplace=True)
    #    demand_data['Timestamp'] = pd.to_datetime(demand_data['Timestamp'], format='%Y-%m-%d %H:%M:%S')
    #    demand_data.set_index('Timestamp', inplace=True)

    #    demand_year = demand_data.index[0].year

    #    index = pd.read_csv(indexfile)
    #    index['Timestamp'] = pd.to_datetime(index['Timestamp'], format='%Y-%m-%d %H:%M:%S')
    #    index.set_index('Timestamp', inplace=True)
        #index.drop(columns=['Unnamed: 0'], inplace=True)

        ## Aggregate by summing over all the hexagons and resampling from 1h to 3h intervals
    #    grouped_demand_data = demand_data.groupby([demand_data.index, 'Daytype']).sum()['Demand (MW)'].groupby([pd.Grouper(freq='3h', level=0), 'Daytype']).mean()

    #    col1.write(grouped_demand_data.index)

        ## Function that returns the appropriate demand for a given day
    #    def select_demand(idx):
    #        col1.write(grouped_demand_data.index)
    #        col1.write(f"B: {idx}")
    #        groupd_idx = (idx.replace(year=demand_year ,day=1),'weekday' if idx.weekday() < 5 else 'weekend')
    #        return grouped_demand_data[groupd_idx]

        ## Build a load profile
    #    target_percentage = 0.03 # This is the percentage (30%) of the demand that we want to fulfill
    #    col1.write("Before start")
    #    col1.write(index)
    #    col1.write("Lets start")
    #    for i in index:
    #        col1.write(i)
    #        col1.write(f"A: {i}")
    #        col1.write(select_demand(i))
    #    total_demand = [select_demand(i) for i in index]
    #    target_load = [target_percentage*p for p in total_demand]
        #print("Max load: " + str(max(target_load)) + " MW")

    #   plt.figure(figsize=(12, 6))  # Sets the figure size
    #   plt.bar(index, total_demand, label='Demand', color='green')  # Plots the load profile against the index
    #   plt.bar(index, target_load, label='Targeted demand', color='blue')  # Plots the load profile against the index
    #   plt.title('Load Profile Across 2025')  # Sets the title of the graph
    #   plt.xlabel('Time')  # Sets the label for the x-axis
    #   plt.ylabel('Demand (MW)')  # Sets the label for the y-axis
    #   plt.grid(True)  # Enables the grid for better readability
    #   plt.legend()  # Adds a legend
        #plt.show()  # Displays the plot
    #   col1.pyplot(plt)
    st_obj.write("Demand...")
