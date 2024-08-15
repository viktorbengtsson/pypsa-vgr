import streamlit as st
from library.config import set_app_config
from library.style import set_app_style

# Set config for app
set_app_config()
set_app_style()

# Define the pages

index = st.Page("index.py", title="Elproduktion", default=True)
about = st.Page("about.py", title="Om oss")
assumptions = st.Page("assumptions.py", title="Läs mer")
cta = st.Page("cta.py", title="Gå vidare")
contact = st.Page("contact.py", title="Kontakt")

pg = st.navigation([index, about, assumptions, cta, contact], position="hidden")
pg.run()