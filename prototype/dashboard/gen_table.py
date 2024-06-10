import numpy as np
import pandas as pd

def size_text(index):
    if index == 0:
        return "turbiner"
    elif index == 1:
        return "turbiner"
    elif index == 2:
        return "hektar"
    elif index == 3:
        return "generatorer"
    elif index == 4:
        return "ton"
    elif index == 5:
        return "elektrolysverk"
    elif index == 6:
        return "parker"
    else:
        return ""

def render_generators_table(st_obj, config):
    data1 = pd.DataFrame({
        '': ['Vindkraft (land)', 'Vindkraft (hav)', 'Solkraft', 'Vätgaskraft', 'Vätgaslagring', 'Vätgas generering', 'Batterilagring'],
        'Kapacitet': [f"{i} MW" for i in np.random.randint(1, 101, size=7)],
        'Storlek': [f"{i} {size_text(index)}" for index, i in enumerate(np.random.randint(1, 101, size=7))],
        'Kostnad': [f"{i} MSEK" for i in np.random.randint(1, 101, size=7)],
        'Driftskostnad': [f"{i} mSEK" for i in np.random.randint(1, 101, size=7)],
        'Kapacitetsfaktor': [f"{i} %" for i in np.random.randint(1, 101, size=7)],
        'Dispatch': [f"{i} MWh" for i in np.random.randint(1, 101, size=7)]
    })
    data1.set_index('', inplace=True)
    st_obj.write(data1)

