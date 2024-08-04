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

def get_plot_keys(columns):
    labels = get_labels()

    main_series_labels = []
    main_series_keys = []
    for col in columns:
        if col != "Backstop":
            main_series_labels.append(labels[col])
            main_series_keys.append(col)

    return [
        main_series_labels,
        main_series_keys,
    ]

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

def get_plot_colors(main_series_keys, use_next_palette = False):

    labels = get_labels()
    labels_length = len(labels)

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

    print(main_series_keys)

    return {k: colors[k] for k in main_series_keys}

def get_plot_label_colors(main_series_keys, use_next_palette = False):

    labels = get_labels()
    labels_length = len(labels)

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

    return {labels[k]: colors[k] for k in main_series_keys}
