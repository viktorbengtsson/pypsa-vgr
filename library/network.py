import pypsa

def build_network(index, resolution, geography, load, assumptions, discount_rate, cf_solar, cf_onwind, cf_offwind, use_offwind, use_h2, h2_initial, biogas):

    def annuity(r, n):
        return r / (1.0 - 1.0 / (1.0 + r) ** n)

    def annualized_capex(asset):
        return (annuity(discount_rate, float(assumptions.loc[(asset, 'lifetime'), 'value'])) + float(assumptions.loc[(asset, 'FOM'), 'value'])) * float(assumptions.loc[(asset, 'capital_cost'), 'value'])

    # Initialize the network
    network = pypsa.Network()
    network.set_snapshots(index)
    network.snapshot_weightings.loc[:, :] = resolution

    # Carriers
    carriers = [
        'AC',
        'onwind',
        'offwind',
        'solar',
        'li-ion',
        'h2',
        'biogas',
        'mixedgas',
        'backstop',
        'import',
        # 'nuclear',
        ]

    carrier_colors = ['black', 'green', 'blue', 'red', 'lightblue', 'grey', 'brown', 'brown', 'white', 'white']#, 'mintgreen']

    network.madd(
        'Carrier',
        carriers,
        color=carrier_colors,
        )

    # Load bus location (center of geography)
    minx, miny, maxx, maxy = geography
    midx = (minx + maxx)/2
    midy = (miny + maxy)/2

    # Add buses to network
    network.add('Bus', 'load-bus', carrier='AC', x=midx, y=midy)
    network.add('Bus', 'renewables-bus', x=midx+0.5, y=midy+0.25)
    network.add('Bus', 'battery-bus', carrier='li-ion', x=midx-0.5, y=midy)
    if use_h2 or biogas > 0:
        network.add('Bus', 'turbine-bus', x=midx, y=midy+0.5)
    if use_h2:
        network.add('Bus', 'h2-bus', carrier='h2', x=midx-0.5, y=midy+0.5)

    # Add load and backstop to Load bus
    network.add('Load', 'load', bus='load-bus',
                p_set=load
                )

    network.add('Generator', 'backstop', carrier='backstop', bus='load-bus',
                p_nom_extendable=True,
                capital_cost=assumptions.loc[('backstop', 'capital_cost'), 'value'],
                marginal_cost=assumptions.loc[('backstop', 'marginal_cost'), 'value'],
                lifetime=assumptions.loc[('backstop', 'lifetime'), 'value'],
                )

    network.add('Generator', 'market', carrier='import', bus='load-bus',
                p_nom_extendable=True,
                capital_cost=0,
                marginal_cost=600,
                lifetime=100
                )

    # Add generators and links to Renewables bus
    network.add('Generator', 'solar', carrier='solar', bus='renewables-bus',
            p_nom_extendable=True, 
            p_max_pu=cf_solar,
            p_nom_mod=assumptions.loc['solar','unit_size'].value,
            capital_cost= annualized_capex('solar'),
            marginal_cost=assumptions.loc[('solar', 'VOM'), 'value'],
            lifetime=assumptions.loc[('solar', 'lifetime'), 'value'],
            )

    network.add('Generator', 'onwind', carrier='onwind', bus='renewables-bus',
                p_nom_extendable=True,
                p_max_pu=cf_onwind,
                p_nom_mod=assumptions.loc['onwind','unit_size'].value,
                capital_cost= annualized_capex('onwind'),
                marginal_cost=assumptions.loc[('onwind', 'VOM'), 'value'],
                lifetime=assumptions.loc['onwind','lifetime'].value,
                )

    if use_offwind:
        network.add('Generator', 'offwind', carrier='offwind', bus='renewables-bus',
                    p_nom_extendable=True,
                    p_max_pu=cf_offwind,
                    p_nom_mod=assumptions.loc['offwind','unit_size'].value,
                    capital_cost= annualized_capex('offwind'),
                    marginal_cost=assumptions.loc[('offwind', 'VOM'), 'value'],
                    lifetime=assumptions.loc['offwind','lifetime'].value,
                    )

    network.add('Link', 'Renewables load link', bus0='renewables-bus', bus1='load-bus',
                p_nom_extendable=use_offwind,
                )

    # Add battery storage, charging, and discharging

    network.add('Link','battery-charge', bus0='renewables-bus', bus1='battery-bus',
                p_nom_extendable = True,
                capital_cost= annualized_capex('battery_inverter'),
                marginal_cost=assumptions.loc['battery_inverter','VOM'].value,
                lifetime=assumptions.loc['battery_inverter','lifetime'].value,
                efficiency = assumptions.loc['battery_inverter','efficiency'].value,
                )

    network.add('Store', 'battery', carrier='li-ion', bus='battery-bus',
                e_initial=100,
                e_nom_extendable=True,
                e_cyclic=True,
                e_min_pu=0.15,
                standing_loss=0.00008, # TODO: Check if this is really per hour as in the documentation or if it is per snapshot
                capital_cost= annualized_capex('battery_storage'),
                marginal_cost=assumptions.loc['battery_storage','VOM'].value,
                lifetime=assumptions.loc['battery_storage', 'lifetime'].value,
                )

    network.add('Link','battery-discharge', carrier='li-ion', bus0='battery-bus', bus1='load-bus',
                p_nom_extendable = True,
                efficiency = assumptions.loc['battery_inverter','efficiency'].value,
                )


    # Add H2 electrolysis, storage, pipline to gas turbine
    if use_h2:
        network.add('Link', 'h2-electrolysis', carrier='h2', bus0='renewables-bus', bus1='h2-bus',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['h2_electrolysis','unit_size'].value,
                    capital_cost= annualized_capex('h2_electrolysis'),
                    marginal_cost=assumptions.loc[('h2_electrolysis', 'VOM'), 'value'],
                    lifetime=assumptions.loc['h2_electrolysis','lifetime'].value,
                    efficiency=assumptions.loc['h2_electrolysis','efficiency'].value,
                    )

        network.add('Store', 'h2', carrier='h2', bus='h2-bus',
                    e_initial=h2_initial,
                    e_nom_extendable=True,
                    e_cyclic=True,
                    capital_cost= annualized_capex('h2_storage'),
                    marginal_cost=assumptions.loc['h2_storage','VOM'].value,
                    lifetime=assumptions.loc['h2_storage','lifetime'].value
                    )

        network.add('Link', 'H2 pipeline', carrier='h2', bus0='h2-bus', bus1='turbine-bus',
                    p_nom_extendable=True,
                    )


    # Add biogas market (generator) and pipeline to gas turbine

    if biogas > 0:
        network.add('Generator', 'biogas-market', carrier='biogas', bus='turbine-bus',
                    p_nom_extendable=True,
                    p_nom_max=biogas,
                    marginal_cost=assumptions.loc['biogas','cost'].value,
                    lifetime=100,
                    )

    # Add gas turbines (we only use the CC gas turbine for now)
    if use_h2 or biogas > 0:
        network.add('Link', 'gas-turbine', carrier='mixedgas', bus0='turbine-bus', bus1='load-bus',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['combined_cycle_gas_turbine','min_size'].value, # New minimal size for generator
                    #p_nom_mod=assumptions.loc['combined_cycle_gas_turbine','unit_size'].value,
                    capital_cost= annualized_capex('combined_cycle_gas_turbine'),
                    marginal_cost=assumptions.loc['combined_cycle_gas_turbine','VOM'].value,
                    lifetime=assumptions.loc['combined_cycle_gas_turbine','lifetime'].value,
                    efficiency=assumptions.loc['combined_cycle_gas_turbine','efficiency'].value,
                    )

        '''
        network.add('Link', 'gasturbine-sc', carrier='mixedgas', bus0='turbine-bus', bus1='load-bus',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['simple_cycle_gas_turbine','unit_size'].value,
                    capital_cost= annualized_capex('simple_cycle_gas_turbine'),
                    marginal_cost=assumptions.loc['simple_cycle_gas_turbine','VOM'].value,
                    lifetime=assumptions.loc['simple_cycle_gas_turbine','lifetime'].value,
                    efficiency=assumptions.loc['simple_cycle_gas_turbine','efficiency'].value,
                    )
        '''

    '''
    ## Add nuclear bus and components (sometimes present)
    if use_nuclear:
        network.add('Bus', 'Nuclear', carrier='nuclear', x=midx, y=midy+0.9)

        # Nuclear power plants in VGR capped at 1 during this period
        network.add('Generator', 'nuclear', carrier='nuclear', bus='Nuclear',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['nuclear_conv','p_nom'].value,
                    p_nom_max=float(assumptions.loc['nuclear_conv','p_nom'].value),
                    capital_cost= annualized_capex('nuclear_conv'),
                    marginal_cost=float(assumptions.loc['nuclear_conv','VOM'].value) + float(assumptions.loc['nuclear_conv','fuel'].value),
                    lifetime=assumptions.loc['nuclear_conv','lifetime'].value,
                    )
        
        num_nuclear_smr = 0
        network.add('Generator', f"{'SMR nuclear'}", carrier='nuclear', bus='Nuclear',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['nuclear_smr','p_nom'].value,
                    p_nom_max=num_nuclear_smr * float(assumptions.loc['nuclear_smr','p_nom'].value),
    #                p_nom=assumptions.loc['nuclear_smr','p_nom'].value,
                    capital_cost= annualized_capex('nuclear_smr'),
                    marginal_cost=float(assumptions.loc['nuclear_smr','VOM'].value) + float(assumptions.loc['nuclear_smr','fuel'].value),
                    lifetime=assumptions.loc['nuclear_smr','lifetime'].value,
                    )

        network.add('Link', 'Nuclear to load', carrier='nuclear', bus0='Nuclear', bus1='load-bus',
                    p_nom_extendable=True,
                    )
    '''

    return network