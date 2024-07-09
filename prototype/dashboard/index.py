import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from streamlit.components.v1 import html

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="PyPSA-VGR 2035"
)
HEIGHT = streamlit_js_eval(js_expressions='screen.height', key = 'SCR_H')
WIDTH = streamlit_js_eval(js_expressions='screen.width', key = 'SCR_W')
if HEIGHT is None:
   HEIGHT = 1080
if WIDTH is None:
   WIDTH = 1920

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none }} 
        body, html {{
            margin: 0;
            padding: 0;
        }}
        #container {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            flex-direction: row;
            z-index: 999991;
        }}
        .frame {{
            border: none;
        }}
        #map-frame {{
            width: 600px;
            height: 100%;
        }}
        #data-frame {{
            height: 100%;
            flex: 1;
        }}
        #map-frame.fullsize {{
            width: 100%;
        }}
        #data-frame.hidden {{
            display: none;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

html(f"""
    <script type="text/javascript">
        document.addEventListener("DOMContentLoaded", function() {{
            if (parent.window.location.search) {{
                const p = new URLSearchParams(parent.window.location.search);
                const geo = p.get("geography")
                if (geo && geo !== "None") {{
                    parent.document.getElementById("map-frame").className = "frame";
                    parent.document.getElementById("data-frame").className = "frame";
                    parent.document.getElementById("map-frame").src = "./map?embedded=true&map=true&width={WIDTH}&height={HEIGHT}&geography=" + geo;
                    parent.document.getElementById("data-frame").src = "./vgr-01?embedded=true&width={WIDTH}&height={HEIGHT}&clear-cache=true&geography=" + geo;
                }}

            }}
        }})
        parent.window.addEventListener("message", function(event) {{
            if (event.data.type === "SET_QUERY_PARAM") {{
                const p = new URLSearchParams(event.data.queryParams);
                const map = p.get("map")
                if (map === "true") {{
                    const geo = p.get("geography")
                    if (!geo || geo === "None") {{
                        parent.document.getElementById("map-frame").className = "frame fullszie";
                        parent.document.getElementById("data-frame").className = "frame hidden";
                    }}
                    else {{
                        parent.document.getElementById("map-frame").className = "frame";
                        parent.document.getElementById("data-frame").className = "frame";
                        const p2 = new URLSearchParams(parent.document.getElementById("data-frame").src);
                        const geo2 = p2.get("geography")
                        if (geo2 !== geo) {{
                            parent.document.getElementById("data-frame").src = "./vgr-01?embedded=true&width={WIDTH}&height={HEIGHT}&clear-cache=true&geography=" + geo;

                            var indexUrl = parent.window.location.protocol + "//" + parent.window.location.host + parent.window.location.pathname + "?geography=" + geo;
                            var indexState = {{ "path": indexUrl }};
                            parent.window.history.pushState(indexState,"",indexUrl);
                        }}   
                    }}
                }}
            }}
        }}, false);
        </script>
    """)

st.markdown(
    f"""<div id="container">
    <iframe id="map-frame" class="frame fullsize" src="./map?embedded=true&map=true&width={WIDTH}&height={HEIGHT}"></iframe>
    <iframe id="data-frame" class="frame hidden" src="./vgr-01?embedded=true&width={WIDTH}&height={HEIGHT}&clear-cache=true&geography=None"></iframe>
</div>                
""",
    unsafe_allow_html=True,
)