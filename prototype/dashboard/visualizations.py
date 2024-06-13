import matplotlib.pyplot as plt
import seaborn as sns

def get_labels():
    return {
        "Backstop" : "Backstop",
        "Biogas market" : "Biogas",
        "Offwind park" : "Vindkraft (hav)",
        "Onwind park" : "Vindkraft (land)",
        "Solar park" : "Sol",
        "H2 storage": "Vätgas",
        "Battery": "Batteri",
        "Gas turbine": "Gas turbin",
        "H2 electrolysis": "Vätgas electrolys",
        "Battery charge": "Batteri laddning",
    }


def get_plot_config(columns, include_demand):

    # Rolling average window size for charts (two weeks)
    window_size=112

    labels = get_labels()

    palette = sns.color_palette('pastel', len(labels)).as_hex()

    colors = {
        "Backstop" : "black",
        "Biogas market" : palette[2],
        "Offwind park" : palette[1],
        "Onwind park" : palette[0],
        "Solar park" : palette[3],
        "H2 storage": palette[4],
        "Battery": palette[5]
    }

    sortorder = {
        "Backstop" : 0,
        "Biogas market" : 3,
        "Offwind park" : 2,
        "Onwind park" : 1,
        "Solar park" : 0,
        "H2 storage": 11,
        "Battery": 10
    }

    main_series_labels = []
    main_series_keys = []
    legend_labels = []
    series_colors = []
    for col in columns:
        legend_labels.append(plt.Line2D([0], [0], marker='o', color='w', label=labels[col], markerfacecolor=colors[col], markersize=10))
        series_colors.append(colors[col])
        main_series_labels.append(labels[col])
        main_series_keys.append(col)

    if include_demand:
        legend_labels.append(plt.Line2D([0], [0], marker='o', color='w', label="Behov", markerfacecolor="black", markersize=10))
        legend_labels.append(plt.Line2D([0], [0], marker='o', color='w', label="Behov (vecko-genomsnitt)", markerfacecolor="#AAAAAA", markersize=10))

    colors = {k: colors[k] for k in main_series_keys}

    return [
        window_size,
        legend_labels,
        main_series_labels,
        main_series_keys,
        series_colors,
        labels,
        colors
    ]
