import streamlit as st
from library.config import set_app_config
from library.style import set_app_style
from library.language import TEXTS

# Set config for app
set_app_config()
set_app_style()

# Define the pages

index = st.Page("index.py", title=TEXTS["Explorer"], default=True)
about = st.Page("about.py", title=TEXTS["About"])
assumptions = st.Page("assumptions.py", title=TEXTS["Assumptions"])
cta = st.Page("cta.py", title=TEXTS["CTA"])

pg = st.navigation([index, about, assumptions, cta])

pg.run()