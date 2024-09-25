import math
from library.language import TEXTS

def round_and_prefix(value, prefix, unit, decimals):
    prefixes = ['', 'k', 'M', 'G', 'T']
    if round(value,9) == 0 or math.isnan(value):
        return "-"
    elif value >= 1_000_000:
        return f"{round(value/1_000_000,decimals):.{decimals}f} {prefixes[prefixes.index(prefix)+2]}{unit}"
    elif value >= 1000:
        return f"{round(value/1_000,decimals):.{decimals}f} {prefixes[prefixes.index(prefix)+1]}{unit}"
    elif value < 1000:
        return f"{round(value,decimals):.{decimals}f} {prefix}{unit}"
    else:
        return f"{round(value,decimals):.{decimals}f} {prefix}{unit}"

def round_and_prettify(value, type):
    units = {
        "solar": 'ha',
        "onwind": TEXTS['turbines'],
        "offwind": TEXTS['turbines'],
        "import": ''
    }

    if math.isinf(value):
        return '-'
    elif value == 0:
        return '-'
    else:
        return f"{round(value,0):,.0f} {units[type]}"

def round_and_format(value):
    if math.isnan(value):
        return '-'
    elif math.isinf(value):
        return '-'
    elif value == 0:
        return '-'
    else:
        return f"{round(value,0):,.0f}"

def round_and_percentage(value):
    if math.isnan(value):
        return '-'
    elif math.isinf(value):
        return '-'
    elif value == 0:
        return '-'
    else:
        return f"{round(value*100,0):,.0f}%"

def scenario(geo, year, self_sufficiency, h2, offwind, biogas):
    return f"geography={geo},target-year={year},self-sufficiency={self_sufficiency},h2={h2},offwind={offwind},biogas-limit={biogas}"

def gen_palette(generator):
    return full_palette().get(generator, "#000000")

def stor_palette(store):
    return full_palette().get(store, "#000000")

def full_palette():
    return {
        'solar': '#FCE849',
        'onwind': "#84B082",
        'offwind': "#60BFFF",
        'biogas-turbine': "#EF476F",
        'biogas-market': "#EF476F",
        'biogas': "#EF476F",
        'gas-turbine': "#EF476F",
        'market': "#B7B5B3",
        'backstop': "#B7B5B3",
        'import': "#B7B5B3",
        'battery': "#E3813D",
        'battery-charge': "#E3813D",
        'battery-discharge': "#E3813D",
        'h2': "#8763B3",
        'h2-electrolysis': "#8763B3",
        'demand': "#010101",
        "ON": "#61AC52",
        "OFF": "#D12D45",
        "NEUTRAL": "#697CCC",
        "SUPER": "#42f5c8",
        "Total land": "#4F5F43",
        "Constructed land": "#565656",
        "Housing": "#A0A0A0",
        "Other buildings": "#98C379",
        "Buildings": "#948169",
        "opacity": 0.75
    }
