import pandas as pd
import numpy as np

# Process assumptions csv to dataframe
def read_assumptions(path, base_year, target_year, base_currency, exchange_rates, discount_rate):
    df = pd.read_csv(path, index_col=list(range(2))).sort_index()
    convert_currency(df, exchange_rates, base_currency)
    # present_values(df, base_year, discount_rate) TODO: We temporarily remove the recalculation of (mostly) 2020 money to 2024 values.
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

    def lambda_mean(group, base_year, target_year):
        if len(group) > 1:
            # Determine bounds for interpolation
            lower_bound = group.loc[group['year'] <= base_year, 'year'].values.max() if len(group.loc[group['year'] <= base_year]) > 0 else base_year
            upper_bound = group.loc[group['year'] >= target_year, 'year'].values.min() if len(group.loc[group['year'] >= target_year]) > 0 else target_year
            years = np.arange(lower_bound, upper_bound + 1)

            # Interpolate value
            value_series = (
                group.set_index('year')['value']
                .reindex(years)
                .interpolate(method='linear')
                .loc[base_year:target_year]
            )

            # Calculate the mean value
            mean_value = value_series.mean()

            # Preserve additional columns (unit, source, comment)
            preserved_cols = group.iloc[0][['unit', 'source', 'comment']].to_dict()
            preserved_cols['value'] = mean_value
            preserved_cols['year'] = 'mean'

            return pd.Series(preserved_cols)
        else:
            # Single value, no interpolation needed
            preserved_cols = group.iloc[0][['unit', 'source', 'comment']].to_dict()
            preserved_cols['value'] = group['value'].values[0]
            preserved_cols['year'] = group['year'].values[0]

            return pd.Series(preserved_cols)

    result = df.groupby(level=[0, 1]).apply(lambda group: lambda_mean(group, base_year, target_year))
    result = result[['value', 'year', 'unit', 'source', 'comment']]  # Explicit column ordering

    return result
