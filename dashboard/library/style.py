import streamlit as st

def set_app_style():
    st.markdown(
        f"""
        <style>
            body, html {{
                margin: 0;
                padding: 0;
            }}
            [data-testid=stSidebar] {{
                background-color: #ffffff;
                border-radius: 5px;  /* Rounded corners */
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);  /* More defined shadow for depth */
            }}

        </style>
        """,
        unsafe_allow_html=True,
    )