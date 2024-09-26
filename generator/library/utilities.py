# Short utility function to check for a file and delete if exists with pathlib
def delete_file(path):
    if path.exists():
        path.unlink()
    else:
        print(f"{path} does not exist")

# Lists all the charge and discharge links (to/from battery and biogas+h2)
def list_links(use_h2, use_biogas):
    links_charge = ['battery-charge']
    links_discharge = ['battery-discharge']
    if use_h2:
        links_charge += ['h2-electrolysis']
    if use_h2 or use_biogas:
        links_discharge += ['gas-turbine']

    return links_charge, links_discharge

# Lists the renewable generator types used in the model
def list_renewables(use_offwind):
    if use_offwind:
        return ['solar', 'onwind', 'offwind']
    else:
        return ['solar', 'onwind']
