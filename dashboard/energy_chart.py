from data_loading import network_data
from visualizations import get_plot_label_colors
import altair as alt

def _get_compare_data(DATA_ROOT, config, pinned):
    GEN_AND_STOR = network_data(DATA_ROOT, config, "energy_compare")
    GEN_AND_STOR_SERIES = network_data(DATA_ROOT, config, "energy_compare_series")

    label_colors = get_plot_label_colors(GEN_AND_STOR_SERIES, pinned)

    GEN_AND_STOR['Color'] = GEN_AND_STOR['Type'].map(label_colors)

    return GEN_AND_STOR

def render_compare_energy_chart(DATA_ROOT, st_obj, config, compare_config):

    data = _get_compare_data(DATA_ROOT, config, False)
    compare_data = _get_compare_data(DATA_ROOT, compare_config, True)

    chart = alt.Chart(data).mark_bar(size=50).encode(
        y=alt.Y('Category:N', title='', sort=[0,1], axis=alt.Axis(labelAngle=0)),
        x=alt.X('Value:Q', title=''),
        color=alt.Color('Color:N', scale=None),
        tooltip=['Category:N', 'Type:N', 'Value:Q'],
        yOffset=alt.value(82)
    )
    chart_compare = alt.Chart(compare_data).mark_bar(size=50).encode(
        y=alt.Y('Category:N', title='', sort=[0,1], axis=alt.Axis(labelAngle=0)),
        x=alt.X('Value:Q', title=''),
        color=alt.Color('Color:N', scale=None),
        tooltip=['Category:N', 'Type:N', 'Value:Q'],
        yOffset=alt.value(30)
    )
    
    combined_chart = alt.layer(chart, chart_compare).properties(
        width=600,
        height=300,
        title=''
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        anchor='middle',
        color='black'
    )

    st_obj.altair_chart(combined_chart, use_container_width=True)
