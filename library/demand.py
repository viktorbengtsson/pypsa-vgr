import math

# This calculation is based on a 2023 estimate from energiforetagen.se that can be fetched here: https://www.energiforetagen.se/pressrum/pressmeddelanden/2023/ny-rapport-sa-moter-vi-sveriges-elbehov-2045/
# It projectes an increase from 140 TWh annually in 2023 to 330 TWh annually in 2045
ENERGY_DEMAND_GROWTH = math.exp(math.log(330/140)/(2045-2023)) - 1

# Caluclate projected energy in MWh annually
# The parameter self_sufficiency ranges from 0 to 2 where the first 0 to 1 denotes fraction of new demand (on top of base demand) and 
def projected_energy(target_year, self_sufficiency):
    base_year = 2023
    base_demand = 19 # TWh per year
    fraction_new = min(self_sufficiency, 1)
    fraction_base = max(0, self_sufficiency - 1)

    return fraction_new * ( base_demand * (1 + ENERGY_DEMAND_GROWTH) ** (target_year - base_year) - base_demand ) + fraction_base * base_demand