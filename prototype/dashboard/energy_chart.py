import pandas as pd
from data_loading import network_data_from_variables
from visualizations import get_plot_config
import seaborn as sns
import altair as alt

def render_energy_chart(st_obj, config):

    NETWORK = network_data_from_variables("../", config)

    GEN = NETWORK.generators_t.p.sum()
    STOR = NETWORK.stores.loc[["H2 storage", "Battery"]]['e_nom_opt']

    gen_columns = [col for idx, col in enumerate(GEN.index) if GEN.iloc[idx].sum() > 0]
    [
        gen_window_size,
        gen_legend_labels,
        gen_main_series_labels,
        gen_main_series_keys,
        gen_series_colors,
        gen_labels,
        gen_colors
    ] = get_plot_config(gen_columns, False)

    gen_total = GEN[[col for col in gen_columns if col in gen_main_series_keys]].sum()
    GEN = GEN[[col for col in gen_columns if col in gen_main_series_keys]] / gen_total * 100
    GEN.index = [col for col in gen_main_series_labels]
    gen_palette = sns.color_palette('pastel', len(GEN.values))

    stor_columns = [col for idx, col in enumerate(STOR.index) if STOR.iloc[idx].sum() > 0]
    [
        stor_window_size,
        stor_legend_labels,
        stor_main_series_labels,
        stor_main_series_keys,
        stor_series_colors,
        stor_labels,
        stor_colors
    ] = get_plot_config(stor_columns, False)

    stor_total = STOR[[col for col in stor_columns if col in stor_main_series_keys]].sum()
    STOR = STOR[[col for col in stor_columns if col in stor_main_series_keys]] / stor_total * 100
    STOR.index = [col for col in stor_main_series_labels]
    stor_palette = sns.color_palette('pastel', len(STOR.values))

    GEN_DATA = pd.DataFrame({'Category': ["Produktion"] * len(GEN.index), 'Type':GEN.index, 'Value':GEN.values, 'Color': gen_palette })
    STOR_DATA = pd.DataFrame({'Category': ["Lagring"] * len(STOR.index),  'Type':STOR.index, 'Value':STOR.values, 'Color': stor_palette })

    data = pd.concat([GEN_DATA, STOR_DATA])
    colors = gen_colors | stor_colors
    main_series_labels = gen_main_series_labels + stor_main_series_labels

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Category:N', title='', sort=[0,1], axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Value:Q', title=''),
        color=alt.Color('Type:N', scale=alt.Scale(domain=main_series_labels, range=list(colors.values())))
            .legend(title="", fillColor="#FFFFFF", strokeColor="#000000", cornerRadius=10),
        tooltip=['Category:N', 'Type:N', 'Value:Q']
    ).properties(
        width=600,
        height=375,
        title='Produktion / lagring (%)'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        anchor='middle',
        color='black'
    )

    st_obj.altair_chart(chart, use_container_width=True)
