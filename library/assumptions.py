import pandas as pd
import numpy as np

# Process assumptions csv to dataframe
def read_assumptions(path, base_year, target_year, base_currency, exchange_rates, discount_rate):
    df = pd.read_csv(path, index_col=list(range(2))).sort_index()
    convert_currency(df, exchange_rates, base_currency)
    present_values(df, base_year, discount_rate)
    output = calculate_means(df, base_year, target_year, "linear")
    return output

# Converts all non-base currencies in assumptions to base currency
def convert_currency(df, rates, base_currency):
    for rate in rates:
        df.loc[df.unit.str.contains(rate),"value"]*=rates[rate] # Do the conversion
        df.loc[df.unit.str.contains(rate), "unit"] = df.loc[df.unit.str.contains(rate), "unit"].str.replace(rate, base_currency) # Replace currency code with base_currency
    return df

# Calculate the present values (base year) of all assumptions
def present_values(df, base_year, discount_rate):
    df.loc[(df.valyear.notnull()) & (df.valyear != base_year), "value"] = df.loc[(df.valyear.notnull()) & (df.valyear != base_year), "value"] / ((1 + discount_rate) ** (df.loc[(df.valyear.notnull()) & (df.valyear != base_year), "valyear"] - base_year))
    df.loc[(df.valyear.notnull()) & (df.valyear != base_year), "valyear"] = base_year

# Calculate the correct means across the build period for all assumptions with time-dependent values
def calculate_means(df, base_year, target_year, build_curve):

    # This function assumes a linear buildout between base year and target year
    def lambda_mean(group, base_year, target_year):
        if len(group) > 1:
            # Calculate the years that bound the range from base_year to target_year
            lower_bound = group.loc[group['year'] <= base_year, 'year'].values.max()
            upper_bound = group.loc[group['year'] >= target_year, 'year'].values.min()
            # Create an array of all the years
            years = np.arange(lower_bound, upper_bound + 1)
            # This line does the following: 1. Select only the years in group that fall within our bound, 2. Set the index to 'year', 3. Reindex series with all years and NaN on years without values 4. Interpolate the missing values 5. Select only our range 6. Calculate the mean
            mean_value = group.loc[(group['year'] >= lower_bound) & (group['year'] <= upper_bound),['value', 'year']].set_index('year')['value'].reindex(years).interpolate(method='linear').loc[base_year:target_year].mean()
            return pd.Series({'value': mean_value, 'year': 'mean'})
        else:
            return pd.Series({'value': group['value'].values[0], 'year': group['year'].values[0]})

    return df.groupby(level=[0,1])[['value', 'year']].apply(lambda group: lambda_mean(group, base_year, target_year))
