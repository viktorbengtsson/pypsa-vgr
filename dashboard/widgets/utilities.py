import math

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
        "onwind": 'turbines',
        "offwind": 'turbines',
        "import": ''
    }

    if math.isinf(value):
        return '-'
    elif value == 0:
        return '-'
    else:
        return f"{round(value,0):,.0f} {units[type]}"

def scenario(geo, year, floor, load, h2, offwind, biogas):
    return f"geography={geo},target-year={year},floor={floor},load-target={load},h2={h2},offwind={offwind},biogas-limit={biogas}"

def gen_palette(generator):
    return full_palette().get(generator, "#000000")

def stor_palette(storage):
    return full_palette().get(storage, "#000000")

def full_palette():
    return {
        'solar': '#FCE849',
        'onwind': "#84B082",
        'offwind': "#60BFFF",
        'biogas_market': "#EF476F",
        'backstop': "#B7B5B3",
        'battery': "#BDFFB5",
        'h2': "#C18EFF"
    }
