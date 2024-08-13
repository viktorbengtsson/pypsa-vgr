import pypsa

def build_network(index, resolution, geography, load, assumptions, cf_solar, cf_onwind, cf_offwind, use_offwind, use_h2, biogas_production_max_nominal):

    def annuity(r, n):
        return r / (1.0 - 1.0 / (1.0 + r) ** n)

    def annualized_capex(asset):
        return (annuity(float(assumptions.loc[('general', 'discount_rate'), 'value']), float(assumptions.loc[(asset, 'lifetime'), 'value'])) + float(assumptions.loc[(asset, 'FOM'), 'value'])) * float(assumptions.loc[(asset, 'capital_cost'), 'value'])

    # Build the network

    ## Initialize the network
    network = pypsa.Network()
    network.set_snapshots(index)
    network.snapshot_weightings.loc[:, :] = resolution

    ## Carriers
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
        # 'nuclear',
        ]

    carrier_colors = ['black', 'green', 'blue', 'red', 'lightblue', 'grey', 'brown', 'brown', 'white']#, 'mintgreen']

    network.madd(
        'Carrier',
        carriers,
        color=carrier_colors,
        )

    ## Load bus location (center of geography)
    minx, miny, maxx, maxy = geography
    midx = (minx + maxx)/2
    midy = (miny + maxy)/2

    ## Add load bus and components (always present)
    network.add('Bus', 'Load bus', carrier='AC', x=midx, y=midy)
    network.add('Load', 'Desired load', bus='Load bus',
                p_set=load
                )

    network.add('Generator', 'backstop', carrier='backstop', bus='Load bus',
                p_nom_extendable=True,
                capital_cost=assumptions.loc[('backstop', 'capital_cost'), 'value'],
                marginal_cost=assumptions.loc[('backstop', 'marginal_cost'), 'value'],
                lifetime=assumptions.loc[('backstop', 'lifetime'), 'value'],
                )

    ## Add battery bus (always present)
    network.add('Bus', 'Battery bus', carrier='li-ion', x=midx-0.5, y=midy)

    ## Add solar bus and components (always present)
    network.add('Bus', 'Solar', x=midx+0.5, y=midy+0.25)

    network.add('Generator', 'solar', carrier='solar', bus='Solar',
            p_nom_extendable=True, 
            p_max_pu=cf_solar,
            p_nom_mod=assumptions.loc['solar','unit_size'].value,
            capital_cost= annualized_capex('solar'),
            marginal_cost=assumptions.loc[('solar', 'VOM'), 'value'],
            lifetime=assumptions.loc[('solar', 'lifetime'), 'value'],
            )

    network.add('Link', 'Solar load link', carrier='solar', bus0='Solar', bus1='Load bus',
                p_nom_extendable=True,
                )

    network.add('Link', 'Solar battery link', carrier='solar', bus0='Solar', bus1='Battery bus',
                p_nom_extendable=True,
                )

    ## Add onwind bus and components (always present)
    network.add('Bus', 'Onwind', x=midx+0.5, y=midy-0.15)

    network.add('Generator', 'onwind', carrier='onwind', bus='Onwind',
                p_nom_extendable=True,
                p_max_pu=cf_onwind,
                p_nom_mod=assumptions.loc['onwind','unit_size'].value,
                capital_cost= annualized_capex('onwind'),
                marginal_cost=assumptions.loc[('onwind', 'VOM'), 'value'],
                lifetime=assumptions.loc['onwind','lifetime'].value,
                )

    network.add('Link', 'Onwind load link', carrier='onwind', bus0='Onwind', bus1='Load bus',
                p_nom_extendable=True,
                )

    network.add('Link', 'Onwind battery link', carrier='onwind', bus0='Onwind', bus1='Battery bus',
                p_nom_extendable=True,
                )

    ### Add offwind bus and components (sometimes present)
    if use_offwind:
        network.add('Bus', 'Offwind', x=midx-1.25, y=midy-0.75)

        network.add('Generator', 'offwind', carrier='offwind', bus='Offwind',
                    p_nom_extendable=use_offwind,
                    p_max_pu=(cf_offwind if use_offwind else [0] * len(cf_offwind)),
                    p_nom_mod=assumptions.loc['offwind','unit_size'].value,
                    capital_cost= annualized_capex('offwind'),
                    marginal_cost=assumptions.loc[('offwind', 'VOM'), 'value'],
                    lifetime=assumptions.loc['offwind','lifetime'].value,
                    )

        network.add('Link', 'Offwind load link', carrier='offwind', bus0='Offwind', bus1='Load bus',
                    p_nom_extendable=use_offwind,
                    )

        network.add('Link', 'Offwind battery link', carrier='offwind', bus0='Offwind', bus1='Battery bus',
                    p_nom_extendable=use_offwind,
                    )

    ## Add battery buses and components (always present)
    network.add('Bus', 'Battery storage', carrier='li-ion', x=midx-0.5, y=midy)

    network.add('Link', 'toBattery', carrier='li-ion', bus0='Load bus', bus1='Battery bus',
                p_nom_extendable=True
                )

    network.add('Link','Battery charge', bus0 = 'Battery bus', bus1 = 'Battery storage',
                p_nom_extendable = True,
                capital_cost= annualized_capex('battery_inverter'),
                marginal_cost=assumptions.loc['battery_inverter','VOM'].value,
                lifetime=assumptions.loc['battery_inverter','lifetime'].value,
                efficiency = assumptions.loc['battery_inverter','efficiency'].value,
                )

    network.add('Store', 'battery', carrier='li-ion', bus='Battery storage',
                e_initial=100,
                e_nom_extendable=True,
                e_cyclic=True,
                e_min_pu=0.15,
                standing_loss=0.00008, # TODO: Check if this is really per hour as in the documentation or if it is per snapshot
                capital_cost= annualized_capex('battery_storage'),
                marginal_cost=assumptions.loc['battery_storage','VOM'].value,
                lifetime=assumptions.loc['battery_storage', 'lifetime'].value,
                )

    network.add('Link','Battery discharge', carrier='li-ion', bus0 = 'Battery storage', bus1 = 'Load bus',
                p_nom_extendable = True,
                efficiency = assumptions.loc['battery_inverter','efficiency'].value,
                )

    ## Add gas turbine bus and components (sometimes present)
    if use_h2 or biogas_production_max_nominal > 0:
        network.add('Bus', 'Gas turbine', x=midx, y=midy+0.5)
        
        network.add('Link', 'gasturbine-sc', carrier='mixedgas', bus0='Gas turbine', bus1='Load bus',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['simple_cycle_gas_turbine','unit_size'].value,
                    capital_cost= annualized_capex('simple_cycle_gas_turbine'),
                    marginal_cost=assumptions.loc['simple_cycle_gas_turbine','VOM'].value,
                    lifetime=assumptions.loc['simple_cycle_gas_turbine','lifetime'].value,
                    efficiency=assumptions.loc['simple_cycle_gas_turbine','efficiency'].value,
                    )

        network.add('Link', 'gasturbine-cc', carrier='mixedgas', bus0='Gas turbine', bus1='Load bus',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['combined_cycle_gas_turbine','unit_size'].value,
                    capital_cost= annualized_capex('combined_cycle_gas_turbine'),
                    marginal_cost=assumptions.loc['combined_cycle_gas_turbine','VOM'].value,
                    lifetime=assumptions.loc['combined_cycle_gas_turbine','lifetime'].value,
                    efficiency=assumptions.loc['combined_cycle_gas_turbine','efficiency'].value,
                    )

    ## Add H2 bus and components (sometimes present)
    if use_h2:
        network.add('Bus', 'H2 bus', carrier='h2', x=midx-0.5, y=midy+0.5)

        network.add('Bus', 'H2 storage', carrier='h2', x=midx-0.5, y=midy+0.5)

        network.add('Link', 'toH2', bus0='Load bus', bus1='H2 bus',
                    p_nom_extendable=True
                    )

        network.add('Link', 'H2 electrolysis', carrier='h2', bus0='H2 bus', bus1='H2 storage',
                    p_nom_extendable=True,
                    p_nom_mod=assumptions.loc['h2_electrolysis','unit_size'].value,
                    capital_cost= annualized_capex('h2_electrolysis'),
                    marginal_cost=assumptions.loc[('h2_electrolysis', 'VOM'), 'value'],
                    lifetime=assumptions.loc['h2_electrolysis','lifetime'].value,
                    efficiency=assumptions.loc['h2_electrolysis','efficiency'].value,
                    )

        network.add('Store', 'h2', carrier='h2', bus='H2 storage',
                    e_initial=(150_000 if use_h2 else 0),
                    e_nom_extendable=use_h2,
                    e_cyclic=True,
                    capital_cost= annualized_capex('h2_storage'),
                    marginal_cost=assumptions.loc['h2_storage','VOM'].value,
                    lifetime=assumptions.loc['h2_storage','lifetime'].value
                    )

        network.add('Link', 'H2 pipeline', carrier='h2', bus0='H2 storage', bus1='Gas turbine',
                    p_nom_extendable=True,
                    )

        network.add('Link', 'Solar H2 link', carrier='solar', bus0='Solar', bus1='H2 bus',
                    p_nom_extendable=True,
                    )

        network.add('Link', 'Onwind H2 link', carrier='onwind', bus0='Onwind', bus1='H2 bus',
                    p_nom_extendable=True,
                    )

    if use_offwind and use_h2:
        network.add('Link', 'Offwind H2 link', carrier='offwind', bus0='Offwind', bus1='H2 bus',
                    p_nom_extendable=use_offwind,
                    )


    ## Add biogas market bus and components (sometimes present)

    if biogas_production_max_nominal > 0:
        network.add('Bus', 'Biogas market', x=midx, y=midy+0.9)

        network.add('Generator', 'biogas_market', carrier='biogas', bus='Biogas market',
                    p_nom_extendable=True,
                    p_nom_max=biogas_production_max_nominal,
                    marginal_cost=assumptions.loc['biogas','cost'].value,
                    lifetime=100,
                    )

        network.add('Link', 'Biogas pipeline', carrier='biogas', bus0='Biogas market', bus1='Gas turbine',
                    p_nom_extendable=True,
                    )
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

        network.add('Link', 'Nuclear to load', carrier='nuclear', bus0='Nuclear', bus1='Load bus',
                    p_nom_extendable=True,
                    )
    '''

    return network