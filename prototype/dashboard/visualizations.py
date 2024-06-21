import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import rgb2hex
import colorsys

def get_labels():
    return {
        "Backstop" : "Backstop",
        "Biogas market" : "Biogas",
        "Offwind park" : "Vindkraft (hav)",
        "Onwind park" : "Vindkraft (land)",
        "Solar park" : "Sol",
        "H2 storage": "Vätgas",
        "Battery storage": "Batteri",
        "Gas turbine": "Gas turbin",
        "H2 electrolysis": "Vätgas electrolys",
        "Battery charge": "Batteri laddning",
        "Biogas input": "Biogas",
        "SMR nuclear": "Kärnkraft",
        "Conventional nuclear": "Kärnkraft",
        "Combined Cycle Gas turbine": "Kombinerad gas turbin",
        "Simple Cycle Gas turbine": "Enkel gas turbin",
        "Total": "Total",
    }

def adjust_lightness(rgb_color, factor):
    h, l, s = colorsys.rgb_to_hls(*rgb_color)
    adjusted_l = max(0, min(1, l * factor))
    return colorsys.hls_to_rgb(h, adjusted_l, s)

def rgb_to_hsl(rgb):
    factor = 1.0  # Increase lightness by 50%
    h, l, s = colorsys.rgb_to_hls(*rgb)
    return h, max(0, min(1, l * factor)), s

def _brighten_colors(colors, use_next_palette):
    if use_next_palette:
        return [rgb2hex(adjust_lightness((r, g, b), 1.12)) for r, g, b in colors]
    else:
        return [rgb2hex(color) for color in colors]

def get_plot_config(columns, include_demand, use_next_palette = False):

    # Rolling average window size for charts (two weeks)
    window_size=112

    labels = get_labels()
    labels_length = len(labels)

    #if not use_next_palette:
    palette = sns.color_palette("pastel6", labels_length)
    stor_palette = sns.color_palette('Set3', 4)

    palette = _brighten_colors(palette, use_next_palette)
    stor_palette = _brighten_colors(stor_palette, use_next_palette)

    colors = {
        "Backstop" : "black",
        "Onwind park" : palette[0],
        "Offwind park" : palette[1],
        "Solar park" : palette[2],
        "SMR nuclear": palette[3],
        "Conventional nuclear": palette[3],
        "Biogas market" : "red", # Are we showing it?
        "Biogas input": palette[4],
        "H2 storage": stor_palette[0],
        "Battery storage": stor_palette[1],
        "Combined Cycle Gas turbine": palette[4],
        "Simple Cycle Gas turbine": palette[4],
    }

    sortorder = {
        "Backstop" : 0,
        "Biogas market" : 3,
        "Offwind park" : 2,
        "Onwind park" : 1,
        "Solar park" : 0,
        "H2 storage": 11,
        "Battery storage": 10,
        "Biogas input": 20,
        "SMR nuclear": 21,
    }

    main_series_labels = []
    main_series_keys = []
    legend_labels = []
    series_colors = []
    for col in columns:
        legend_labels.append(plt.Line2D([0], [0], marker='o', color='w', label=labels[col], markerfacecolor=colors[col], markersize=10))
        series_colors.append(colors[col])
        if col != "Backstop":
            main_series_labels.append(labels[col])
            main_series_keys.append(col)

    if include_demand:
        legend_labels.append(plt.Line2D([0], [0], marker='o', color='w', label="Behov", markerfacecolor="black", markersize=10))
        legend_labels.append(plt.Line2D([0], [0], marker='o', color='w', label="Behov (vecko-genomsnitt)", markerfacecolor="#AAAAAA", markersize=10))

    colors = {k: colors[k] for k in main_series_keys}
    label_colors = {labels[k]: colors[k] for k in main_series_keys}

    return [
        window_size,
        legend_labels,
        main_series_labels,
        main_series_keys,
        series_colors,
        labels,
        colors,
        label_colors
    ]
