def render_visualizations(st_col1, st_col2, data_root, geography, variables):

    if len(geography) == 0:
        st_col1.write("VÄLJ KOMMUNER TILL VÄNSTER")
    else:
        #config = _config_from_variables(data_root, variables, geography)

        st_col1.write(variables)
        #st_col1.write(config)

        st_col1.write("Render stuff")

        st_col2.write("Render widgets")
    