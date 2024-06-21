import pandas as pd
import numpy as np
from data_loading import network_data_from_variables
from visualizations import get_plot_config
import seaborn as sns
import altair as alt

def _get_data(config, pinned):
    NETWORK = network_data_from_variables("../", config)

    generator_index = NETWORK.generators.index.difference(['Backstop', 'Biogas input'])

    GEN = pd.concat([
        NETWORK.generators.loc[NETWORK.generators.index.isin(generator_index)][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']],
        NETWORK.links.loc[['Combined Cycle Gas turbine', 'Simple Cycle Gas turbine']][['capital_cost', 'marginal_cost', 'lifetime', 'p_nom_opt', 'p_nom_mod']]
    ])
    GEN['annual_cost'] = np.where(GEN['p_nom_opt'] != 0, GEN['capital_cost'] * GEN['p_nom_opt'], 0)
    GEN = GEN["annual_cost"]

    STOR = NETWORK.stores.loc[["H2 storage", "Battery storage"]][['capital_cost', 'marginal_cost', 'lifetime', 'e_nom_opt']]
    STOR['annual_cost'] = np.where(STOR['e_nom_opt'] != 0, STOR['capital_cost'] * STOR['e_nom_opt'], 0)
    STOR = STOR["annual_cost"]

    gen_columns = [col for idx, col in enumerate(GEN.index) if GEN.iloc[idx].sum() > 0]
    [
        gen_window_size,
        gen_legend_labels,
        gen_main_series_labels,
        gen_main_series_keys,
        gen_series_colors,
        gen_labels,
        gen_colors,
        gen_label_colors
    ] = get_plot_config(gen_columns, False, pinned)

    GEN = GEN[[col for col in gen_columns if col in gen_main_series_keys]] / 1_000_000
    GEN.index = [col for col in gen_main_series_labels]

    stor_columns = [col for idx, col in enumerate(STOR.index) if STOR.iloc[idx].sum() > 0]
    [
        stor_window_size,
        stor_legend_labels,
        stor_main_series_labels,
        stor_main_series_keys,
        stor_series_colors,
        stor_labels,
        stor_colors,
        stor_label_colors
    ] = get_plot_config(stor_columns, False, pinned)

    STOR = STOR[[col for col in stor_columns if col in stor_main_series_keys]] / 1_000_000
    STOR.index = [col for col in stor_main_series_labels]

    GEN_DATA = pd.DataFrame({'Category': ["Produktion (MSEK)"] * len(GEN.index), 'Type':GEN.index, 'Value':GEN.values })
    STOR_DATA = pd.DataFrame({'Category': ["Lagring (MSEK)"] * len(STOR.index),  'Type':STOR.index, 'Value':STOR.values })

    data = pd.concat([GEN_DATA, STOR_DATA])
    data['Color'] = data['Type'].map(gen_label_colors | stor_label_colors)

    return data

def render_compare_energy_chart(st_obj, config, compare_config):

    data = _get_data(config, False)
    compare_data = _get_data(compare_config, True)

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

def render_energy_chart(st_obj, config):

    NETWORK = network_data_from_variables("../", config)

    GEN = NETWORK.generators_t.p.sum()
    STOR = NETWORK.stores.loc[["H2 storage", "Battery storage"]]['e_nom_opt']

    gen_columns = [col for idx, col in enumerate(GEN.index) if GEN.iloc[idx].sum() > 0]
    [
        gen_window_size,
        gen_legend_labels,
        gen_main_series_labels,
        gen_main_series_keys,
        gen_series_colors,
        gen_labels,
        gen_colors,
        label_colors
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
        stor_colors,
        label_colors
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
        color=alt.Color('Type:N', scale=alt.Scale(domain=main_series_labels, range=list(colors.values())), legend=None),
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
