import streamlit as st
from pathlib import Path
from library.language import TEXTS, LANGUAGE

# Load page data
content_path = Path(__file__).parent / 'content'
body = (content_path / f"cta_{LANGUAGE}.md").read_text(encoding='utf-8')

# Page layout and content
st.title(TEXTS["CTA"])

st.markdown(body)
