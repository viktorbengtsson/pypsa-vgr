import numpy as np

# Calculate the biogas purchase/import limit
def calculate_biogas_max(biogas_limit, load, gas_efficiency, method):
    return np.mean(load)*biogas_limit/gas_efficiency    

## Add a constraint on biogas energy (annual)
def add_biogas_constraint(model, demand, biogas_limit, gas_efficiency):
    total_e = demand.sum()
    biogas_e = model.variables['Generator-p'].loc[:,'biogas-market'].sum()*gas_efficiency
    biogas_limit_e = total_e * biogas_limit

    model.add_constraints(biogas_e <= biogas_limit_e, name="biogas_limit")

## Add a constraint on energy imports from market
def add_self_sufficiency_constraint(model, demand, self_sufficiency):
    total_e = demand.sum()
    market_e = model.variables['Generator-p'].loc[:,'market'].sum()
    non_sufficiency_e = total_e * (1 - self_sufficiency)

    model.add_constraints(market_e <= non_sufficiency_e, name="self_sufficiency_constraint")

## Add battery charge/discharge ratio constraint
def add_battery_flow_constraint(model, battery_efficiency):
    link_capacity = model.variables["Link-p_nom"]
    lhs = link_capacity.loc["battery-charge"] - battery_efficiency * link_capacity.loc["battery-discharge"]
    
    model.add_constraints(lhs == 0, name="Link-battery_fix_ratio")
