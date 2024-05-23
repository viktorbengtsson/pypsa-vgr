import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def render_capacity_chart(st_col1, st_col2):

    data1 = pd.DataFrame({
        'Timestamp': np.arange(np.datetime64('2023-01-01'), np.datetime64('2024-01-01'), dtype='datetime64[W]'),
        'Vindkraft (land)': np.random.randint(30, 50, size=52) / 100,
        'Vindkraft (hav)': np.random.randint(40, 90, size=52) / 100,
        'Solkraft': np.random.randint(0, 80, size=52) / 100,
        'Vätgaskraft': np.random.randint(0, 10, size=52) / 100,
        'Vätgaslagring': np.random.randint(0, 10, size=52) / 100,
        'Vätgas generering': np.random.randint(0, 10, size=52) / 100,
        'Batterilagring': np.random.randint(10, 15, size=52) / 100
    })
    data1.set_index('Timestamp', inplace=True)

    col1, col2 = st_col2.columns([1, 1])

    options = col1.multiselect(
        'Energislag',
        data1.columns.tolist(),
        default=data1.columns.tolist()
    )
    col2.selectbox("Visa data",
    ("Kapacitetsfaktor", "MW", "Kostnad"))

    if options:
        plt.figure(figsize=(12, 6))

        for column in options:
            plt.plot(data1.index, data1[column], label=column)

        plt.xlabel('Date')
        plt.ylabel('Kapacitetsfactor')
        plt.title('Produktion')
        plt.legend(loc='upper left')
        plt.grid(True)

        st_col1.pyplot(plt)
    else:
        st_col1.write("Välj minst 1 energislag")

