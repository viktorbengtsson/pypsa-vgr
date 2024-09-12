import streamlit as st

def set_app_style():
    st.markdown(
        f"""
        <style>
            body, html {{
                margin: 0;
                padding: 0;
            }}
            [data-testid=stAppViewBlockContainer] {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            @media (min-width: 1500px) {{
                [data-testid=stAppViewBlockContainer] {{
                    padding-left: 6rem;
                    padding-right: 6rem;
                }}
            }}
            [data-testid=stSidebar] {{
                background-color: #ffffff;
                border-radius: 5px;  /* Rounded corners */
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);  /* More defined shadow for depth */
            }}
            [data-testid=stButton] {{
                position: relative;
                overflow: visible;
            }}
            [data-testid="stBaseButton-secondary"] {{
                float: right;
                border: 0;
            }}
            [aria-label="help icon"] {{
                font-size: 1.35rem;
            }}

        </style>
        """,
        unsafe_allow_html=True,
    )