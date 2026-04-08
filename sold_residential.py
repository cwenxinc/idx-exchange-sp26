import pandas as pd
import matplotlib.pyplot as plt

sold = pd.read_csv('raw-data/sold_raw.csv')
sold['PropertyType'].unique() # consistent with listings: residential, residential lease, residential income, commercial lease, commericla sale, business opportunity, manufactured in park, land
sold.shape # 587516 records

# retain residential transactions
mask_residential = sold['PropertyType'] == 'Residential'
sold_residential = sold[mask_residential]
sold_residential.shape # 394799 records left

# flag fields with high percentages of missing values
null_counts = sold_residential.isnull().sum()
null_percs = sold_residential.isnull().mean() * 100
null_table = pd.DataFrame({
    'null count': null_counts,
    'null percentage': null_percs
})
mask_high_null_perc = null_percs > 90
null_table[mask_high_null_perc] # 17 fields have over 90% of values missing
                                # however this list does not contain any key field (OK)
fields_high_null_perc = sold_residential.columns[mask_high_null_perc]

# inspect the distribution of key numeric fields
sold_residential['MlsStatus'].unique() # confirm that all transactions are closed to avoid producing misleading results
key_fields = ['ClosePrice', 'OriginalListPrice', # sold dataset does not include list price, DOM, and living area
              'BedroomsTotal', 'BathroomsTotalInteger', 'LotSizeAcres', 'YearBuilt']
# percentiles
sold_residential[key_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # again, some properties have abnormally high bedroom or bathroom counts
                                                                               # latest transactions occurred this year (OK)
                                                                               # NOTE: original list price vs list price?
# TODO: histograms
for field in key_fields: 
    sold_residential[field].hist(bins=30)
    plt.title(f'Histogram of {field}')
    plt.xlabel(field)
    plt.ylabel('Frequency')
    plt.show()
# TODO: boxplots
for field in key_fields:
    sold_residential.boxplot(column=field)
    plt.title(f'Boxplot of {field}')
    plt.ylabel(field)
    plt.show()

# add in mortgage rate data
# derive year-month key from close date
sold_residential['year_month'] = pd.to_datetime(sold_residential['CloseDate']).dt.to_period('M')
# pull mortgage rate data from FRED and then create a matching year-month key
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url)
mortgage.columns = ['date', 'rate_30yr_fixed']
mortgage['year_month'] = pd.to_datetime(mortgage['date']).dt.to_period('M')
mortgage_monthly = mortgage.groupby('year_month')['rate_30yr_fixed'].mean().reset_index()
# merge monthly sold transactions and mortgage rates
sold_residential_with_rates = sold_residential.merge(mortgage_monthly, on='year_month', how='left')
sold_residential_with_rates.shape # right dimensions
sold_residential_with_rates.columns # rates properly added as a column
sold_residential_with_rates['rate_30yr_fixed'].isnull().sum() # no null values after merging (OK)

sold_residential_with_rates.to_csv("raw-data/sold_residential_with_rates_raw.csv", index=False)