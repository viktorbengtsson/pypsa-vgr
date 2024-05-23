import numpy as np
import pandas as pd

def render_generators_table(st_obj):
    data1 = pd.DataFrame({
        '': ['Vindkraft (land)', 'Vindkraft (hav)', 'Solkraft', 'Vätgaskraft', 'Vätgaslagring', 'Vätgas generering', 'Batterilagring'],
        'Kapacitet': np.random.randint(1, 101, size=7),
        'Storlek': np.random.randint(1, 101, size=7),
        'Kostnad': np.random.randint(1, 101, size=7),
        'Driftskostnad': np.random.randint(1, 101, size=7),
        'Kapacitetsfaktor': np.random.randint(1, 101, size=7),
        'Dispatch': np.random.randint(1, 101, size=7)
    })
    data1.set_index('', inplace=True)
    st_obj.write(data1)
