import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def render_energy_chart(st_obj):

    data1 = pd.DataFrame({
        'Category': ['Vindkraft (land)', 'Vindkraft (hav)', 'Solkraft', 'Batterilagring'],
        'Value': np.random.randint(1, 101, size=4)
    })

    plt.pie(data1['Value'], labels=data1['Category'], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.legend().set_visible(False)

    st_obj.pyplot(plt) 
