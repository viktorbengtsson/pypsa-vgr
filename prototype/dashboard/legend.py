import pandas as pd
from data_loading import network_data_from_variables
from visualizations import get_plot_config
import seaborn as sns
import altair as alt

def render_legend(st_obj, config, use_next_palette):

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
    ] = get_plot_config(gen_columns, False, use_next_palette)

    gen_total = GEN[[col for col in gen_columns if col in gen_main_series_keys]].sum()
    GEN = GEN[[col for col in gen_columns if col in gen_main_series_keys]] / gen_total * 100
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
        label_colors
    ] = get_plot_config(stor_columns, False, use_next_palette)

    stor_total = STOR[[col for col in stor_columns if col in stor_main_series_keys]].sum()
    STOR = STOR[[col for col in stor_columns if col in stor_main_series_keys]] / stor_total * 100
    STOR.index = [col for col in stor_main_series_labels]

    series_length = len(GEN.values) + len(STOR.values)
    
    GEN_DATA = pd.DataFrame({'Category': ["Produktion"] * len(GEN.index), 'Type':GEN.index, 'Value':GEN.values })
    STOR_DATA = pd.DataFrame({'Category': ["Lagring"] * len(STOR.index),  'Type':STOR.index, 'Value':STOR.values })

    data = pd.concat([GEN_DATA, STOR_DATA])
    colors = gen_colors | stor_colors
    main_series_labels = gen_main_series_labels + stor_main_series_labels

    chart = alt.Chart(data).mark_circle(size=0).encode(
        color=alt.Color('Type:N', scale=alt.Scale(domain=main_series_labels, range=list(colors.values())))
            .legend(title="", fillColor="#FFFFFF", symbolOpacity=1, symbolType="square", orient='left'),
    ).configure_view(strokeWidth=0
    ).properties(
        width=100,
        height=110,
        title=''
    )

    st_obj.altair_chart(chart, use_container_width=True)
