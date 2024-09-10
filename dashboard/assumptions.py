import streamlit as st
import pandas as pd
from pathlib import Path
from library.config import set_data_root
from library.language import TEXTS, LANGUAGE

# Load page data
data_root = set_data_root()
assumptions = pd.read_csv(data_root / 'assumptions.csv')

content_path = Path(__file__).parent / 'content'
body = (content_path / f"assumptions_{LANGUAGE}.md").read_text(encoding='utf-8')

# Page layout and content
st.title(TEXTS["Assumptions"])

st.markdown(body)

st.dataframe(assumptions)
