import pandas as pd

listed = pd.read_csv('raw-data/listed_raw.csv')
listed['PropertyType'].unique() # manufactured in park, commercial sale, commercial lease, residential, residential lease, residential income, business opportunity, land
listed.shape # 852963 records

"""
Part I: Filter for residential listings
"""

mask_residential = listed['PropertyType'] == 'Residential'
listed_residential = listed[mask_residential]
listed_residential.shape # 540183 records left


"""
Part II: Merge in mortgage rate data
"""

# derive year-month key from listing contract date
listed_residential['year_month'] = pd.to_datetime(listed_residential['ListingContractDate']).dt.to_period('M')

# pull mortgage rate data from FRED and then create a matching year-month key
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed'] # most recent rate dates to 2026-04-09
mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = mortgage.groupby('year_month')['rate_30yr_fixed'].mean().reset_index()

# merge monthly listings and mortgage rates
listed_residential_with_rates = listed_residential.merge(mortgage_monthly, on='year_month', how='left')
listed_residential_with_rates.columns
listed_residential_with_rates.shape
listed_residential_with_rates['rate_30yr_fixed'].isnull().sum() # no null values after merging (OK)

listed_residential_with_rates.to_csv("raw-data/listed_residential_with_rates_raw.csv", index=False)


"""
Part III: Data validation
"""

listed_full = pd.read_csv("raw-data/listed_residential_with_rates_raw.csv")

# (i) flag fields with a significant amount of null values
null_counts = listed_full.isnull().sum()
null_percs = listed_full.isnull().mean() * 100
null_table = pd.DataFrame({
    'null count': null_counts,
    'null percentage': null_percs
})
mask_high_null_perc = null_percs > 90
null_table[mask_high_null_perc] # 13 fields have over 90% of values missing
                                # however this list does not contain any key field (OK)
fields_high_null_perc = listed_full.columns[mask_high_null_perc]
# look into core fields
null_table.loc[['ListPrice', 'ClosePrice', # 73 percent missing close price (OK), none missing list price (GOOD)
                'DaysOnMarket', # none missing DOM (GOOD)
                'LivingArea']] # 10 percent missing living area

# (ii) flag redundant fields
fields_redundant = [field for field in listed_full.columns if field.endswith('.1')]

# (iii) validate data types
# date fields
date_fields = ['ListingContractDate', 'PurchaseContractDate', 'CloseDate', 'ContractStatusChangeDate']
listed_full[date_fields] = listed_full[date_fields].apply(pd.to_datetime)
# numeric fields
numeric_fields = ['ClosePrice', 'OriginalListPrice', 'ListPrice', 'DaysOnMarket', 
                  'LivingArea', 'BedroomsTotal', 'BathroomsTotalInteger', 'LotSizeAcres', 'YearBuilt', 
                  'Latitude', 'Longitude', 
                  'rate_30yr_fixed']
listed_full[numeric_fields] = listed_full[numeric_fields].apply(pd.to_numeric)

# (iv) flag records with invalid numeric values
# look at pricing
listed_full['invalid_price_flag'] = listed_full['ListPrice'] <= 0 # none
# look at living space
listed_full['missing_living_space_flag'] = listed_full['LivingArea'].isna()
listed_full['invalid_living_space_flag'] = (listed_full['LivingArea'] <= 0) | (listed_full['BedroomsTotal'] < 0) | (listed_full['BathroomsTotalInteger'] < 0) # 359 records
# look at time to sell
listed_full['negative_dom_flag'] = listed_full['DaysOnMarket'] < 0 # 29 records
# look at coordinates
listed_full['missing_coord_flag'] = listed_full['Latitude'].isna() | listed_full['Longitude'].isna() # 80145 records
listed_full['zero_coord_flag'] = (listed_full['Latitude'] == 0) | (listed_full['Longitude'] == 0) # 60 records
ca_lat = [32.5, 43]
ca_lon = [-124.26, -114.8]
listed_full['outside_ca_flag'] = (~listed_full['Longitude'].between(ca_lon[0], ca_lon[1])) | (~listed_full['Latitude'].between(ca_lat[0], ca_lat[1])) # 81077 records

# (v) flag records with invalid date order
# NOTE: listing data represent the entire market supply and likely include properties that do no follow a linear timeline (e.g., pulled off market at some point)
#       date validation is thus much more complicated
# NOTE: comparing a value with NaN returns False and does not affect flagging
listed_full['MlsStatus'].unique() # active, active under contract, pending, closed, coming soon
mask_pending = listed_full['MlsStatus'] == "Pending"
listed_full['pending_listing_after_purchase_flag'] = listed_full[mask_pending]['ListingContractDate'] > listed_full[mask_pending]['PurchaseContractDate'] # 38 records
mask_closed = listed_full['MlsStatus'] == "Closed"
listed_full['closed_purchase_after_close_flag'] = listed_full[mask_closed]['PurchaseContractDate'] > listed_full[mask_closed]['CloseDate'] # 245 records
listed_full['closed_listing_after_close_flag'] = listed_full[mask_closed]['ListingContractDate'] > listed_full[mask_closed]['CloseDate'] # 72 records
mask_undercontract = listed_full['MlsStatus'] == "ActiveUnderContract"
listed_full['undercontract_listing_after_purchase_flag'] = listed_full[mask_undercontract]['ListingContractDate'] > listed_full[mask_undercontract]['PurchaseContractDate'] # 16 records

listed_full.columns # confirm flags
listed_full.to_csv("raw-data/listed_residential_with_rates_flagged.csv", index=False)


"""
Part IV: Data cleaning
"""

# (i) remove invalid records
mask_valid = ~(
    listed_full['invalid_price_flag'] |
    listed_full['invalid_living_space_flag'] | 
    listed_full['negative_dom_flag'] | 
    listed_full['zero_coord_flag'] | listed_full['outside_ca_flag'] |
    listed_full['closed_listing_after_close_flag'] | listed_full['closed_purchase_after_close_flag'] | 
    listed_full['pending_listing_after_purchase_flag'] | listed_full['undercontract_listing_after_purchase_flag']
)
listed_valid = listed_full[mask_valid]
listed_valid.shape # 458507 records left

# (ii) remove outliers
# NOTE: percentiles are calculated for valid records ONLY
core_fields = ['ListPrice', 'ClosePrice', 'LivingArea', 'DaysOnMarket']
listed_valid[core_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])

q1 = listed_valid[core_fields].quantile(0.25)
q3 = listed_valid[core_fields].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
listed_valid['outlier_flag'] = ((listed_valid[core_fields] < lower) | (listed_valid[core_fields] > upper)).any(axis=1) # 84109 records
listed_reliable = listed_valid[~listed_valid['outlier_flag']]
listed_reliable.shape # 374398 records left
listed_reliable[core_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # mean and median have gone down across all core fields

# (iii) remove records missing core values
mask_core_missing = listed_reliable['missing_living_space_flag']
listed_core_not_missing = listed_reliable[~mask_core_missing]
listed_core_not_missing.shape # 374178 records left
listed_core_not_missing.shape[0] / listed_full.shape[0] # 69 percent of records retained

# (iv) remove unneeded fields
# redundant fields
listed_clean = listed_core_not_missing.drop(columns=fields_redundant)
listed_clean.shape[1] # 11 fields removed
# fields with a significant amount of missing values
listed_clean = listed_clean.drop(columns=fields_high_null_perc)
listed_clean.shape[1] # 13 fields removed
# flag fields 
mask_flag = listed_clean.columns.str.endswith("_flag")
fields_flag = listed_clean.columns[mask_flag]
listed_clean = listed_clean.drop(columns=fields_flag)
listed_clean.shape[1] # 62 fields left

listed_clean.to_csv("clean-data/listed_residential_with_rates_clean.csv", index=False)