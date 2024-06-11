import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from data_loading import deep_data_from_variables

def render_energy_chart(st_obj, config):

    data1 = pd.DataFrame({
        'Category': ['Vindkraft (land)', 'Vindkraft (hav)', 'Solkraft'],
        'Value': np.random.randint(1, 101, size=3)
    })

    plt.pie(data1['Value'], labels=data1['Category'], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.legend().set_visible(False)

    st_obj.pyplot(plt) 

    [
        ASSUMPTIONS,
        DEMAND,
        NETWORK,
        STATISTICS,
        CUTOUT,
        SELECTION,
        EEZ,
        AVAIL_SOLAR,
        AVAIL_ONWIND,
        AVAIL_OFFWIND,
        AVAIL_CAPACITY_SOLAR,
        AVAIL_CAPACITY_ONWIND,
        AVAIL_CAPACITY_OFFWIND,
    ] = deep_data_from_variables("../", config)

    NETWORK.optimize()
    #statistics = NETWORK.statistics()

    fig, ax = plt.subplots()
    NETWORK.statistics.supply(comps=["Generator"], aggregate_time=False).droplevel(0).iloc[
        :, :4
    ].div(1e3).T.plot.area(
        title="Generation in GW",
        ax=ax,
        legend=False,
        linewidth=0,
    )
    ax.legend(bbox_to_anchor=(1, 0), loc="lower left", title=None, ncol=1)
    st_obj.pyplot(fig)
