LANGUAGE = "sv"

ALL_TEXTS = {
    "Nominal effect": { "sv": "Nominell effekt" },
    "Units required": { "sv": "Antal enheter" },

    "solar": { "sv": "Solkraft", "en": "Solar" },
    "onwind": { "sv": "Vindkraft (land)", "en": "Onshore wind" },
    "offwind": { "sv": "Vindkraft (hav)", "en": "Offshore wind" },
    "biogas_market": { "sv": "Biogas", "en": "Biogas" },
    "backstop": { "sv": "Tillförlitlighet", "en": "Backstop" },
    "battery": { "sv": "Batteri", "en": "Battery" },
    "h2": { "sv": "Vätgas", "en": "Hydrogen" },

    "turbines": { "sv": "turbiner" },

    "Production target": { "sv": "Elproduktionsmål" },

    "Offshore": { "sv": "Havsvind" },
    "Biogas": { "sv": "Biogas" },

    "Compare": { "sv": "Jämför" },
    "Close compare": { "sv": "Stäng jämförelse" },
    "Generator types": { "sv": "Generatorer" },
    "Storage types": { "sv": "Lagring" },
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