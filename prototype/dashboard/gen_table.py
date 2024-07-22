import streamlit as st
from data_loading import network_data

def render_generators_table(DATA_ROOT, st_obj, config):
    
    TABLE = network_data(DATA_ROOT, config, "table")

    st_obj.dataframe(TABLE.data, column_config={
        "Totalkostnad": st.column_config.ProgressColumn(
            "Totalkostnad",
            help="Total kostnad med procent-andel av total",
            format="%f MSEK",
            min_value=0,
            max_value=TABLE.sum_total_cost,
        )
    })
