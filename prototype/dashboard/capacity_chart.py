import pandas as pd
from data_loading import network_data_from_variables, demand_data_from_variables
from visualizations import get_plot_config
import altair as alt

def render_capacity_chart(st_col1, st_col2, config):

    DEMAND = demand_data_from_variables("../", config)
    NETWORK = network_data_from_variables("../", config)

    GEN = NETWORK.generators_t.p.abs()
    
    #Exclude if we have no data
    columns = [column for column in GEN.columns if GEN[column].sum() > 0]
    [
        window_size,
        legend_labels,
        main_series_labels,
        main_series_keys,
        series_colors,
        labels,
        colors
    ] = get_plot_config(columns, True)

    #options = col1.multiselect(
    #    'Category',
    #    main_series_labels,
    #    default=main_series_labels
    #)

    #col2.selectbox("", ("Behov (MW)", "Kostnad (MSEK)"))

    #if options:
    index_to_exclude = [] #[idx for idx, col in enumerate(columns) if not main_series_labels[main_series_keys.index(col)] in options]
    GEN = GEN[[col for idx, col in enumerate(columns) if idx not in index_to_exclude]]

    DEMAND_rolling = DEMAND.rolling(window=window_size, center=True).mean()
    GEN_rolling = GEN.rolling(window=window_size, center=True).mean()
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
        color=alt.Color('Category:N', scale=alt.Scale(domain=main_series_labels, range=list(colors.values())))
        .legend(title="", orient='bottom-left', fillColor="#FFFFFF", strokeColor="#000000", cornerRadius=10)
    )

    # Line chart for single line data
    line_chart_rolling = base.mark_line(color='black').encode(
        y=alt.Y('Demand_rolling:Q', title=''),
    )
    line_chart = base.mark_line(color='grey', strokeWidth=1, opacity=0.5).encode(
        y=alt.Y('Demand:Q', title=''),
    )

    # Combine the charts
    combined_chart = alt.layer(area_chart, line_chart, line_chart_rolling).properties(
        width=800,
        height=450,
        title="Elproduktion/konsumption (MW)"
    ).configure_title(
        anchor='middle',
        color='black'
    )

    # Display the chart in Streamlit
    st_col1.altair_chart(combined_chart, use_container_width=True)

#    else:
#        st_col1.write("Välj minst ett energislag")


