import pandas as pd
from data_loading import demand_data_from_variables, network_data, get_assumption_data
from visualizations import get_labels, get_plot_colors, get_plot_label_colors, get_plot_keys
import altair as alt
import json
from urllib import request

chart_height = 350

def render_capacity_chart(DATA_ROOT, st_col1, config):

    DEMAND = demand_data_from_variables(DATA_ROOT, config)
    GEN = network_data(DATA_ROOT, config, "capacity")

    # Rolling average window size for charts (two weeks)
    window_size=112

    #Exclude if we have no data
    columns = [column for column in GEN.columns if GEN[column].sum() > 0]
    labels = get_labels()
    [
        main_series_labels,
        main_series_keys,
    ] = get_plot_keys(columns)
    colors = get_plot_colors(main_series_keys)

    DO_ROLLING = True

    GEN_rolling = GEN.rolling(window=window_size, center=True).mean() if DO_ROLLING else GEN
    DEMAND_rolling = DEMAND.rolling(window=window_size, center=True).mean() if DO_ROLLING else DEMAND
    if DO_ROLLING:
        for col in DEMAND.columns:
            DEMAND_rolling.loc[DEMAND_rolling.index[0], col] = DEMAND[col].iloc[0::7].mean()
            DEMAND_rolling.loc[DEMAND_rolling.index[-1], col] = DEMAND[col].iloc[-1::-9].mean()
        for col in GEN.columns:
            GEN_rolling.loc[GEN_rolling.index[0], col]= GEN[col].iloc[0::7].mean()
            GEN_rolling.loc[GEN_rolling.index[-1], col] = GEN[col].iloc[-1::-9].mean()
        DEMAND_rolling = DEMAND_rolling.interpolate()
        GEN_rolling = GEN_rolling.interpolate()

    data = {
        "Date": GEN.index,
        "Demand_rolling": DEMAND_rolling["se3"],
        "Demand": DEMAND["se3"]
    }

    for col in GEN_rolling.columns:
        data[labels[col]] = GEN_rolling[col].values

    data = pd.DataFrame(data)

    # Melt the data for Altair
    melted_data = data.melt(id_vars=['Date', 'Demand_rolling', 'Demand'], value_vars=main_series_labels, var_name='Category', value_name='Value')

    #melted_data['Category'] = melted_data['Category'].map(labels)

    # Create an Altair chart
    base = alt.Chart(melted_data).encode(
        x=alt.X('Date:T', title=''),
    )

    # Stacked area chart for two categories
    area_chart = base.mark_area().encode(
        y=alt.Y('sum(Value):Q', stack='zero'),
        color=alt.Color('Category:N', scale=alt.Scale(domain=main_series_labels, range=list(colors.values())), legend=None)
    )

    # Line chart for single line data
    line_chart_rolling = base.mark_line(color='black').encode(
        y=alt.Y('Demand_rolling:Q', title=''),
    )
    line_chart = base.mark_line(color='grey', strokeWidth=1, opacity=0.5).encode(
        y=alt.Y('Demand:Q', title=''),
    )

    with request.urlopen('https://raw.githubusercontent.com/d3/d3-format/master/locale/sv-SE.json') as f:
        sv_format = json.load(f)
    with request.urlopen('https://raw.githubusercontent.com/d3/d3-time-format/master/locale/sv-SE.json') as f:
        sv_time_format = json.load(f)

    # Combine the charts
    layer = alt.layer(area_chart, line_chart, line_chart_rolling) if DO_ROLLING else alt.layer(area_chart, line_chart)
    combined_chart = layer.properties(
        width=800,
        height=chart_height,
        title="Elproduktion/konsumption (MWh)"
    ).configure_title(
        anchor='middle',
        color='black'
    ).interactive()

    combined_chart["usermeta"] = {
        "embedOptions": {
            "formatLocale": sv_format,
            "timeFormatLocale": sv_time_format,
        }
    }

    st_col1.altair_chart(combined_chart, use_container_width=True)

def _get_compare_capacity_chart(DATA_ROOT, config, pinned = False):
    GEN = network_data(DATA_ROOT, config, "capacity_monthly")

    #Exclude if we have no data
    columns = [column for column in GEN.columns if GEN[column].sum() > 0]
    labels = get_labels()
    [
        main_series_labels,
        main_series_keys,
    ] = get_plot_keys(columns)
    label_colors = get_plot_label_colors(main_series_keys, pinned)

    data = {}

    for col in GEN.columns:
        data[labels[col]] = GEN[col].values

    return [
        GEN.index,
        data,
        main_series_labels,
        label_colors
    ]

def render_compare_capacity_chart(DATA_ROOT, st_col1, config, compare_config):

    DEMAND = demand_data_from_variables(DATA_ROOT, config)
    parameters = get_assumption_data(DATA_ROOT)
    parameters.set_index(['technology', 'parameter'], inplace=True)

    DEMAND = DEMAND['se3'].resample('ME').sum()*3 / 1_000

    [index, GEN, main_series_labels, colors] = _get_compare_capacity_chart(DATA_ROOT, config)
    [index, COMPARE_GEN, compare_main_series_labels, compare_colors] = _get_compare_capacity_chart(DATA_ROOT, compare_config, True)
    
    data = {
        "Date": index.strftime('%b').tolist(),
        "Demand": DEMAND,
    }
    data_compare = {
        "Date": index.strftime('%b').tolist(),
    }

    for col in GEN:
        data[col] = GEN[col]
    for col in COMPARE_GEN:
        data_compare[col] = COMPARE_GEN[col]


    data = pd.DataFrame(data)
    melted_data = data.melt(id_vars=['Date', 'Demand'], value_vars=main_series_labels, var_name='Category', value_name='Value')
    melted_data['Color'] = melted_data['Category'].map(colors)

    data_compare = pd.DataFrame(data_compare)
    melted_data_compare = data_compare.melt(id_vars=['Date'], value_vars=compare_main_series_labels, var_name='Category', value_name='Value')
    melted_data_compare['Color'] = melted_data_compare['Category'].map(compare_colors)

    base = alt.Chart(melted_data).encode(
        x=alt.X('Date:N', title=''),
    )
    base_compare = alt.Chart(melted_data_compare).encode(
        x=alt.X('Date:N', title='', axis=alt.Axis(labelOffset=-15,labelAngle=0,labelAlign="center")),
    )

    # Stacked area chart for two categories
    bar_chart = base.mark_bar(size=30).encode(
        y=alt.Y('sum(Value):Q', stack='zero'),
        tooltip=[
            alt.Tooltip('Category:N'),
            alt.Tooltip('Value:Q', format='.0f')
        ],
        color=alt.Color('Color:N', scale=None),
    )
    bar_chart_compare = base_compare.mark_bar(size=30,binSpacing=1).encode(
        y=alt.Y('sum(Value):Q', stack='zero'),
        tooltip=[
            alt.Tooltip('Category:N'),
            alt.Tooltip('Value:Q', format='.0f')
        ],
        color=alt.Color('Color:N', scale=None),
        xOffset=alt.value(12)
    )

    # Line chart for single line data
    line_chart = base.mark_line(color='black').encode(
        y=alt.Y('Demand:Q', title=''),
        xOffset=alt.value(29)
    )

    # Combine the charts
    combined_chart = alt.layer(bar_chart, bar_chart_compare, line_chart).properties(
        width=800,
        height=chart_height,
        title="Elproduktion/konsumption (TWh)"
    ).configure_title(
        anchor='middle',
        color='black'
    )

    # Display the chart in Streamlit
    st_col1.altair_chart(combined_chart, use_container_width=True)

#    else:
#        st_col1.write("Välj minst ett energislag")
