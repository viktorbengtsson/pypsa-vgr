import pypsa
import pickle

def create_and_store_optimize(config):
    scenario_config=config["scenario"]
    DATA_PATH=scenario_config["data-path"]
    NETWORK = pypsa.Network()
    NETWORK.import_from_netcdf(f"../{DATA_PATH}/network.nc")

    use_offwind = bool(scenario_config["network-offwind"])

    model = NETWORK.optimize.create_model()
    
    generator_capacity = model.variables["Generator-p_nom"]
    link_capacity = model.variables["Link-p_nom"]
    link_flow = model.variables["Link-p"]
    store_level = model.variables["Store-e"]
    
    
    '''
    ## Solar link capacity
    solar_link_constraint = generator_capacity.loc['Solar park'] - link_capacity.loc['Solar link']
    model.add_constraints(solar_link_constraint == 0, name="Solar_park-solar_link-match")
    
    ## Onwind link capacity
    onwind_link_constraint = generator_capacity.loc['Onwind park'] - link_capacity.loc['Onwind link']
    model.add_constraints(onwind_link_constraint == 0, name="Onwind_park-onwind_link-match")
    
    ## Offwind link capacity
    offwind_link_constraint = generator_capacity.loc['Offwind park'] - link_capacity.loc['Offwind link']
    model.add_constraints(offwind_link_constraint == 0, name="Offwind_park-offwind_link-match")
    
    ## H2 input + H2 store >= H2 output
    #h2_flow_constraint = link_flow.loc["H2 electrolysis"] + store_level.loc['H2 storage'] - link_flow.loc["H2 pipeline"]
    #model.add_constraints(h2_flow_constraint >= 0, name="H2_flow_constraint")
    '''

    ## Offwind constraint
    if use_offwind:
        offwind_percentage = 0.5

        offwind_constraint = (1 - offwind_percentage) / offwind_percentage * generator_capacity.loc['Offwind park'] - generator_capacity.loc['Onwind park']
        model.add_constraints(offwind_constraint == 0, name="Offwind_constraint")

    ## Battery charge/discharge ratio
    lhs = link_capacity.loc["Battery charge"] - NETWORK.links.at["Battery charge", "efficiency"] * link_capacity.loc["Battery discharge"]
    model.add_constraints(lhs == 0, name="Link-battery_fix_ratio")

#    NETWORK.optimize.add_load_shedding(marginal_cost=200)
    
    NETWORK.optimize.solve_model(solver_name='highs')

    statistics = NETWORK.statistics()
    statistics.to_pickle(f"../{DATA_PATH}/statistics.pkl")

    NETWORK.export_to_netcdf(f"../{DATA_PATH}/network.nc")
