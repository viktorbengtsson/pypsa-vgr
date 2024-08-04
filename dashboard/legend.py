from data_loading import network_data
from visualizations import get_plot_colors
import altair as alt

def render_legend(DATA_ROOT, st_obj, config, use_next_palette):

    GEN_AND_STOR = network_data(DATA_ROOT, config, "energy_compare")
    GEN_AND_STOR_SERIES = network_data(DATA_ROOT, config, "energy_compare_series")

    colors = get_plot_colors(GEN_AND_STOR_SERIES, use_next_palette)

    chart = alt.Chart(GEN_AND_STOR).mark_circle(size=0).encode(
        color=alt.Color('Type:N', scale=alt.Scale(domain=list(GEN_AND_STOR_SERIES.values()), range=list(colors.values())))
            .legend(title="", fillColor="#FFFFFF", symbolOpacity=1, symbolType="square", orient='left'),
    ).configure_view(strokeWidth=0
    ).properties(
        width=100,
        height=110,
        title=''
    )

    st_obj.altair_chart(chart, use_container_width=True)
