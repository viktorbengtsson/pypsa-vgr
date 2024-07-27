import streamlit as st
import pandas as pd
from data_loading import network_data
from visualizations import get_plot_colors
import altair as alt


def _create_pie(pie_data, highlighted_category):
    base = alt.Chart(pie_data).encode(
        theta=alt.Theta(field='value', type='quantitative'),
        color=alt.condition(
            alt.FieldOneOfPredicate(field='category', oneOf=highlighted_category),
            alt.Color('color:N', scale=None),
            alt.value('transparent')
        )
    )
    pie = base.mark_arc().properties(
        width=100,
        height=100,
        title=''
    )
    border = alt.Chart(pd.DataFrame({'value': [100]})).mark_arc(
        outerRadius=39,
        stroke='black',
        strokeWidth=1,
        fill=None
    ).encode(
        theta=alt.Theta('value:Q', stack=None)
    ).properties(
        width=100,
        height=100
    )
    chart = alt.layer(pie, border).properties(
        width=100,
        height=100,
        title=''
    )

    return chart

def render_gen_widget(st_obj, header, key, data, countSuffix, compare_data, pie_data = None, biogas_price = None):
    with st_obj.container(border=True):
        st.title(header)
        if compare_data is None:
            chart = _create_pie(pie_data, key)
            st.altair_chart(chart)

            capacity = data.loc[key, "p_nom_opt"].sum()
            count = data.loc[key, "generators"].sum()
            if biogas_price is None:
                price = data.loc[key, "annual_cost"].sum() / data.loc[key, "energy_produced"].sum() / 1000 if data.loc[key, "energy_produced"].sum() > 0 else 0
            else:
                price = biogas_price
            st.metric(f"{price:.2f} kr/kWh", f"{count:.0f} {countSuffix}", delta=f"{capacity:.0f} MW", delta_color="off")
        else:
            count = data.loc[key, "generators"].sum()
            compare_count = compare_data.loc[key, "generators"].sum()
            delta = count - compare_count
            st.metric("", f"{count:.0f} {countSuffix}", delta=f"{delta:.0f} {countSuffix}", label_visibility="collapsed", delta_color=("off" if delta == 0 else "normal"))

def render_stor_widget(st_obj, header, key, data, compare_data, pie_data = None):
    with st_obj.container(border=True):
        st.title(header)
        if compare_data is None:
            #chart = _create_pie(pie_data, key)
            #st.altair_chart(chart)

            capacity = data.loc[key, "p_nom_opt"].sum() / 1_000
            price = data.loc[key, "annual_cost"].sum() / 1_000_000
            st.metric(f"{price:.0f} MSEK", f"{capacity:.1f} GWh", delta="", delta_color="off", label_visibility="collapsed")
        else:
            capacity = data.loc[key, "p_nom_opt"].sum() / 1_000
            compare_capacity = compare_data.loc[key, "p_nom_opt"].sum() / 1_000
            delta = capacity - compare_capacity
            st.metric("", f"{capacity:.1f} GWh", delta=f"{delta:.1f} GWh", label_visibility="collapsed", delta_color=("off" if delta == 0 else "normal"))

def render_other_widget(st_obj, header, value, fraction):
    with st_obj.container(border=True):
        st.title(header)
        percentage = fraction * 100
        st.metric(f"{value:.3f} TWh", f"{percentage:.2f} %", delta="", delta_color="off")

def _get_data(DATA_ROOT, config):
    WIDGETS = network_data(DATA_ROOT, config, "widgets")

    if WIDGETS is None:
        return

    gen_colors = get_plot_colors(["Onwind park", "Offwind park", "Solar park", "Combined Cycle Gas turbine", "Simple Cycle Gas turbine", "Conventional nuclear", "SMR nuclear"], False)
    stor_colors = get_plot_colors(["H2 storage", "Battery storage"], False)

    return WIDGETS + [gen_colors, stor_colors]

def render_widgets(DATA_ROOT, st_obj, config, compare_config):
    st.markdown(
        f"""
        <style>
            h1 {{
                line-height: 1;
                font-size: 1em;
                padding: 0 0 0.5em 0;
                color: #888888;
                font-weight: normal;
                text-transform: uppercase;
            }}
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
                min-height: {0.51 if compare_config is None else 0}rem;
            }}
            div[data-testid="stDataFrame"] {{
                margin-top: 2rem;
            }}
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stArrowVegaLiteChart"] {{
                position: absolute;
                margin-right: -0.75rem;
                right: 0;
            }}
            @media screen and (max-width: 1100px) {{
                div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stArrowVegaLiteChart"] {{
                    display: none;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    [generators_compare, stores_compare, biogas_price, backstop_total, backstop_fraction, curtailment_total, curtailment_fraction, gen_colors, store_colors] = _get_data(DATA_ROOT, compare_config) if compare_config is not None else [None, None, None, None, None, None, None, None, None]
    [generators, stores, biogas_price, backstop_total, backstop_fraction, curtailment_total, curtailment_fraction, gen_colors, store_colors] = _get_data(DATA_ROOT, config)

    if compare_config is None:
        col1, col2, col3 = st_obj.columns([1,1,1], gap="small")

        gen_total = generators["p_nom_opt"].sum()
        gen_pie_data = pd.DataFrame({
            'category': generators.index,
            'value': generators["p_nom_opt"] / gen_total * 100
        })

        store_total = stores["p_nom_opt"].sum()
        store_pie_data = pd.DataFrame({
            'category': stores.index,
            'value': stores["p_nom_opt"] / store_total * 100,
        })

        gen_pie_data['color'] = gen_pie_data['category'].map(gen_colors)
        store_pie_data['color'] = store_pie_data['category'].map(store_colors)

        render_gen_widget(col1, "Vindkraftverk (land)", ["Onwind park"], generators, "st", generators_compare, gen_pie_data)
        render_gen_widget(col2, "Vindkraftverk (hav)", ["Offwind park"], generators, "st", generators_compare, gen_pie_data)
        render_gen_widget(col1, "Solpark", ["Solar park"], generators, "ha", generators_compare, gen_pie_data)
        render_gen_widget(col2, "Biogas", ["Combined Cycle Gas turbine", "Simple Cycle Gas turbine"], generators, "st", generators_compare, gen_pie_data, biogas_price)
        render_gen_widget(col1, "Kärnkraftverk (SMR)", ["Conventional nuclear", "SMR nuclear"], generators, "st", generators_compare, gen_pie_data)

        render_stor_widget(col3, "Vätgas", ["H2 storage"], stores, stores_compare, store_pie_data)
        render_stor_widget(col3, "Batteri", ["Battery storage"], stores, stores_compare, store_pie_data)

        render_other_widget(col3, "Backstop", backstop_total, backstop_fraction)
        render_other_widget(col3, "Spill", curtailment_total, curtailment_fraction)
    else:
        col1, col2, col3, col4 = st_obj.columns([1,1,1,1], gap="small")

        render_gen_widget(col1, "Vindkraftverk (land)", ["Onwind park"], generators, "st", generators_compare)
        render_gen_widget(col2, "Vindkraftverk (hav)", ["Offwind park"], generators, "st", generators_compare)
        render_gen_widget(col3, "Solpark", ["Solar park"], generators, "ha", generators_compare)
        render_gen_widget(col4, "Biogas", ["Combined Cycle Gas turbine", "Simple Cycle Gas turbine"], generators, "st", generators_compare)
        render_gen_widget(col1, "Kärnkraftverk (SMR)", ["Conventional nuclear", "SMR nuclear"], generators, "st", generators_compare)

        render_stor_widget(col3, "Vätgas", ["H2 storage"], stores, stores_compare)
        render_stor_widget(col4, "Batteri", ["Battery storage"], stores, stores_compare)

def render_total_widgets(st_obj, config, compare_config):
    data = pd.DataFrame({'Aktivt val': ["Stor", "30345 MSEK", "A", "B", "C"], 'Jämförelse':["Liten", "3423 MSEK", "Aj", "Bj", "Cj"] })
    data.reset_index(drop=True)
    data.index = ['Biogas', 'Total kost', 'Total prod', 'Backstop', 'Spill']
    st_obj.dataframe(data, use_container_width=True)