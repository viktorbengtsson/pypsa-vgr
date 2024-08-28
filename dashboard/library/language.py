LANGUAGE = "sv"

ALL_TEXTS = {
    "Effect": { "sv": "Effekt" },
    "units_required_solar": { "en": "Area (ha)", "sv": "Yta (ha)"},
    "units_required_onwind": { "en": "Turbines", "sv": "Turbiner"},
    "units_required_offwind": { "en": "Turbines", "sv": "Turbiner"},
    "units_required_biogas-market": { "en": "Turbines", "sv": "Gas turbiner"},
    "units_required_battery": { "en": "Something", "sv": "Nåt"},
    "units_required_h2": { "en": "Something", "sv": "Nåt"},
    "curtailment": { "en": "Curtailment (%)", "sv": "Spill (%)"},

    "solar": { "sv": "Solkraft", "en": "Solar" },
    "onwind": { "sv": "Vindkraft (land)", "en": "Onshore wind" },
    "offwind": { "sv": "Vindkraft (hav)", "en": "Offshore wind" },
    "biogas-market": { "sv": "Biogas", "en": "Biogas" },
    "biogas": { "sv": "Biogas", "en": "Biogas" },
    "backstop": { "sv": "Tillförlitlighet", "en": "Backstop" },
    "battery": { "sv": "Batteri", "en": "Battery" },
    "battery-discharge": { "sv": "Batteri", "en": "Battery" },
    "battery-charge": { "sv": "Batteri", "en": "Battery" },
    "h2": { "sv": "Vätgas", "en": "Hydrogen" },

    "turbines": { "sv": "turbiner" },

    "Production target": { "sv": "Elproduktionsmål" },

    "Offshore": { "sv": "Havsvind" },
    "Biogas": { "sv": "Biogas" },

    "Compare": { "sv": "Jämför" },
    "Close compare": { "sv": "Stäng jämförelse" },
    "Generator types": { "sv": "Generatorer" },
    "Stores types": { "sv": "Lagring" },
    "demand_metric_text": { 
        "en": "Demand is fully met in {fully_length} months: {fully_months}. Average for the remaining months is {average_percentage}%. The worst month is {min_months} where {min_percentage}% of the demand is met.",
        "sv": "Behov uppfyllt till fullo i {fully_length} månader: {fully_months}. Övriga månader är behovet uppfyllt till {average_percentage}%. Den sämsta månaden är {min_months} där {min_percentage}% av behovet är uppfyllt."
    },
    "Performance": { "sv": "Prestanda" },
    "Sufficiency": { "sv": "Tillförlitlighet" },
    "Days below": { "sv": "Otillräckliga dagar" },
    "Number of days": { "sv": "Antal dagar" },
    "Levelized Cost of Energy": { },
    "Store capacity": { "sv": "Lagringskapacitet" },
    "Production": { "sv": "Produktion" },
    "Overall": { "sv": "Total" },
    "Stores": { "sv": "Lagring" },
    "Demand": { "sv": "Behov" },
    "Met need": { "sv": "Uppfyllt behov" },
    "Unmet need": { "sv": "Ej uppfyllt behov" },
    "days_below_hover": { "sv": "I %{x} dagar täcktes %{y} ej", "en": "In %{x} days %{y} wasn't met" }
}

ALL_MONTHS = {
    "January": { "sv": "Januari" },
    "February": { "sv": "Februari" },
    "March": { "sv": "Mars" },
    "April": { "sv": "April" },
    "May": { "sv": "Maj" },
    "June": { "sv": "Juni" },
    "July": { "sv": "Juli" },
    "August": { "sv": "August" },
    "September": { "sv": "September" },
    "October": { "sv": "Oktober" },
    "November": { "sv": "November" },
    "December": { "sv": "December" },
}

TEXTS = {key: value.get(LANGUAGE, key) for key, value in ALL_TEXTS.items()}

MONTHS = [value.get(LANGUAGE, key) for key, value in ALL_MONTHS.items()]