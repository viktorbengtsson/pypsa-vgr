import math
from library.language import TEXTS

def round_and_prefix(value, prefix, unit):
    prefixes = ['', 'k', 'M', 'G', 'T']
    
    if value >= 1_000_000:
        return f"{round(value/1_000_000,0):.0f} {prefixes[prefixes.index(prefix)+2]}{unit}"
    elif value >= 1000:
        return f"{round(value/1_000,0):.0f} {prefixes[prefixes.index(prefix)+1]}{unit}"
    elif value < 1000:
        return f"{round(value,0):.0f} {prefix}{unit}"
    else:
        return f"{round(value,0):.0f} {prefix}{unit}"
    
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

def scenario(geo, year, floor, load, h2, offwind, biogas):
    return f"geography={geo},target-year={year},floor={floor},load-target={load},h2={h2},offwind={offwind},biogas-limit={biogas}"

def gen_palette(generator):
    return full_palette().get(generator, "#000000")

def stor_palette(store):
    return full_palette().get(store, "#000000")

def full_palette():
    return {
        'solar': '#FCE849',
        'onwind': "#84B082",
        'offwind': "#60BFFF",
        'biogas-market': "#EF476F",
        'biogas': "#EF476F",
        'gas-turbine': "#EF476F",
        'backstop': "#B7B5B3",
        'battery': "#E3813D",
        'battery-charge': "#E3813D",
        'battery-discharge': "#E3813D",
        'h2': "#8763B3",
        'h2-electrolysis': "#8763B3",
        'demand': "#010101",
        "ON": "#61AC52",
        "OFF": "#D12D45",
        "NEUTRAL": "#5574F7"
    }
