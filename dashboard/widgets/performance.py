import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from library.config import set_data_root
from widgets.utilities import scenario, full_palette, round_and_prefix
from library.language import TEXTS, MONTHS

def _text_sufficiency(data):
    data["Months"] = MONTHS

    fully = data[data["Value"] == 1.0]
    average = data[data["Value"] < 1.0]["Value"].mean()
    min = data.loc[data['Value'].idxmin()]
    
    text = TEXTS["demand_metric_text"].format(
        fully_length=f"{len(fully)}",
        fully_months=", ".join(fully["Months"]),
        average_percentage="{0:.2f}".format(average * 100),
        min_months=min["Months"],
        min_percentage="{0:.2f}".format(min["Value"] * 100)
    )
    st.markdown(f'<p style="font-size:14px;">{text}</p>', unsafe_allow_html=True)

def _performance_chart(data):
    color_mapping = full_palette()

    total_value = 1 + data.loc['Curtailment (of total)','Value']

    fig = make_subplots()

    fig.add_trace(
        go.Bar(
            x=[data.loc['Sufficiency','Value']],
            marker_color=color_mapping["ON"],
            opacity=color_mapping['opacity'],
            name=TEXTS["Met need"],
            hovertemplate=(
                "<b>" + TEXTS["Met need"] + "</b><br><extra></extra>"
                "" + TEXTS["Percentage"] + ": %{x:.2%}<br>"
                "" + TEXTS["Energy"] + ": " + round_and_prefix(data.loc['Produced energy','Value'], 'M', 'Wh', 2)
            ),
            orientation='h',
            legendrank=3

        ),
    )
    fig.add_trace(
        go.Bar(
            x=[data.loc['Shortfall','Value']],
            marker_color=color_mapping["import"],
            opacity=color_mapping['opacity'],
            name=TEXTS["Unmet need"],
            hovertemplate=(
                "<b>" + TEXTS["Unmet need"] + "</b><br><extra></extra>"
                "" + TEXTS["Percentage"] + ": %{x:.2%}<br>"
                "" + TEXTS["Energy"] + ": " + round_and_prefix(data.loc['Imported energy','Value'], 'M', 'Wh', 2)
            ),
            orientation='h',
            legendrank=2
        ),
    )
    fig.add_trace(
        go.Bar(
            x=[data.loc['Curtailment (of total)','Value']],
            marker_color=color_mapping["SUPER"],
            opacity=color_mapping['opacity'],
            name=TEXTS["Super power"],
            hovertemplate=(
                "<b>" + TEXTS["Super power"] + "</b><br><extra></extra>"
                "" + TEXTS["Percentage"] + ": %{x:.2%}<br>"
                "" + TEXTS["Energy"] + ": " + round_and_prefix(data.loc['Curtailed energy','Value'], 'M', 'Wh', 2)
            ),
            orientation='h',
            legendrank=1
        ),
    )

    fig.update_annotations(font_size=16, font_color="black", height=60)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=1)
    fig.update_xaxes(dict(
        title=None,
        tickmode='array',
        tickvals=[0, 0.25, 0.50, 0.75, 1, total_value],
        tickformat='.0%',
    ))

    fig.update_layout(
        height=220,
        barmode='stack',        
        margin=dict(t=0, b=20, l=10, r=10),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.55,
            xanchor='center',
            x=0.5
        )
    )

    st.plotly_chart(fig, config={'displayModeBar': False})

def performance_widget(geo, target_year, self_sufficiency, h2, offwind, biogas_limit, modal):
    # State management
    data_root = set_data_root()

    fname = data_root / scenario(geo, target_year, self_sufficiency, h2, offwind, biogas_limit) / 'performance' / "performance_metrics.csv.gz"
    if fname.is_file():
        data = pd.read_csv(fname, compression='gzip')
        data.rename(columns={'Unnamed: 0': 'type'}, inplace=True)
        data.set_index('type', inplace=True)

    with st.container(border=True):
        st.markdown(f'<p style="font-size:16px;">{TEXTS["Performance"]}</p>', unsafe_allow_html=True)

        _performance_chart(data)

        if st.button(":material/help:", key='performance'):
            modal('performance')
