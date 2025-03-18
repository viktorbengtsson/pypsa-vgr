import streamlit as st
from pathlib import Path
from library.api import read_csv
from library.language import TEXTS, LANGUAGE
from library.config import get_default_variables

if 'variables' not in st.session_state:
    initial_load = True

    st.session_state['variables'] = get_default_variables(st.query_params)

variables = st.session_state['variables']

# Load page data
#data_root = set_data_root()
assumptions = read_csv(f'assumptions,target-year={variables["target_year"]}.csv.gz', compression='gzip')
landuse = read_csv(f'markanvandning.csv.gz', compression='gzip')
content_path = Path(__file__).parent / 'content'
body = (content_path / f'assumptions_{LANGUAGE}.md').read_text(encoding='utf-8')
landcontent = (content_path / f'landassumptions_{LANGUAGE}.md').read_text(encoding='utf-8')

# Page layout and content
st.title(TEXTS["Assumptions"])

st.markdown(body)

st.dataframe(assumptions)

st.markdown(landcontent)

st.dataframe(landuse)

# Persist session values and query string
st.query_params['target_year'] = str(variables['target_year'])

st.session_state['variables'] = variables