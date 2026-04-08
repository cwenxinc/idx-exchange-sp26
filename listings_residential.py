import pandas as pd
import matplotlib.pyplot as plt

listings = pd.read_csv('raw-data/listings_raw.csv')
listings['PropertyType'].unique() # manufactured in park, commercial sale, commercial lease, residential, residential lease, residential income, business opportunity, land
listings.shape # 853979 records

# retain residential listings
mask_residential = listings['PropertyType'] == 'Residential'
listings_residential = listings[mask_residential]
listings_residential.shape # 540791 records left
 
# flag fields with high percentages of null values
null_counts = listings_residential.isnull().sum()
null_percs = listings_residential.isnull().mean() * 100
null_table = pd.DataFrame({
    'null count': null_counts,
    'null percentage': null_percs
})
mask_high_null_perc = null_percs > 90
null_table[mask_high_null_perc] # 13 fields have over 90% of values missing
                                # however this list does not contain any key field (OK)
fields_high_null_perc = listings_residential.columns[mask_high_null_perc]

# inspect the distribution of key numeric fields
key_fields = ['ClosePrice', 'ListPrice', 'OriginalListPrice', 'DaysOnMarket', # market-related fields
              'LivingArea', 'LotSizeAcres', 'BedroomsTotal', 'BathroomsTotalInteger', 'YearBuilt'] # property-related fields
# percentiles
listings_residential[key_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # some properties have abnormally high bedroom or bathroom counts (e.g., max 94 bedrooms; max 2208 bathrooms)
                                                                                   # some properties have year built in the future (e.g., max 2028)
# TODO: histograms
for field in key_fields: 
    listings_residential[field].hist(bins=30)
    plt.title(f'Histogram of {field}')
    plt.xlabel(field)
    plt.ylabel('Frequency')
    plt.show()
# TODO: boxplots
for field in key_fields:
    listings_residential.boxplot(column=field)
    plt.title(f'Boxplot of {field}')
    plt.ylabel(field)
    plt.show()

# add in mortgage rate data
# derive year-month key from listing contract date
listings_residential['year_month'] = pd.to_datetime(listings_residential['ListingContractDate']).dt.to_period('M')
# pull mortgage rate data from FRED and then create a matching year-month key
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url) # NOTE: parse_dates=['DATE'] returns ValueError
mortgage.columns = ['date', 'rate_30yr_fixed'] # most recent rate dates to 2026-04-02
mortgage['year_month'] = pd.to_datetime(mortgage['date']).dt.to_period('M')
mortgage_monthly = mortgage.groupby('year_month')['rate_30yr_fixed'].mean().reset_index()
# merge monthly listings and mortgage rates
listings_residential_with_rates = listings_residential.merge(mortgage_monthly, on='year_month', how='left')
listings_residential_with_rates.columns
listings_residential_with_rates.shape
listings_residential_with_rates['rate_30yr_fixed'].isnull().sum() # no null values after merging (OK)

listings_residential_with_rates.to_csv("raw-data/listings_residential_with_rates_raw.csv", index=False)