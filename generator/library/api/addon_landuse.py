import pandas as pd

def select_and_store_land_use(land_path, land_file, data_path, geo):
    land_use = pd.read_csv(land_path / land_file, compression='gzip', index_col='Kod')
    land_use.loc[geo.split(':')[-1]].to_csv(data_path / 'landuse.csv.gz', compression='gzip')