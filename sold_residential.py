import pandas as pd

sold = pd.read_csv('raw-data/sold_raw.csv')
sold['PropertyType'].unique() # residential, residential lease, residential income; commercial lease, commercial sale; business opportunity; manufactured in park; land
sold.shape # 591733 records

"""
Part I: Filter for residential transactions
"""

mask_residential = sold['PropertyType'] == 'Residential'
sold_residential = sold[mask_residential]
sold_residential.shape # 397603 records left


"""
Part II: Merge in mortgage rate data
"""

# derive year-month key from close date
sold_residential['year_month'] = pd.to_datetime(sold_residential['CloseDate']).dt.to_period('M')

# pull mortgage rate data from FRED and create a matching year-month key
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed']
mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = mortgage.groupby('year_month')['rate_30yr_fixed'].mean().reset_index()

# merge monthly sold transactions and mortgage rates
sold_residential_with_rates = sold_residential.merge(mortgage_monthly, on='year_month', how='left')
sold_residential_with_rates.shape
sold_residential_with_rates.columns
sold_residential_with_rates['rate_30yr_fixed'].isnull().sum() # no null values after merging (OK)

sold_residential_with_rates.to_csv("raw-data/sold_residential_with_rates_raw.csv", index=False)


"""
Part III: Data validation
"""

sold_full = pd.read_csv('raw-data/sold_residential_with_rates_raw.csv')
sold_full['MlsStatus'].unique() # confirm that all transactions are indeed closed

# (i) flag fields with a significant amount of missing values
null_counts = sold_full.isnull().sum()
null_percs =  sold_full.isnull().mean() * 100
null_table = pd.DataFrame({
    'null count': null_counts,
    'null percentage': null_percs
})
mask_high_null_perc = null_percs > 90
null_table[mask_high_null_perc] # 17 fields have over 90 percent of values missing
                                # however this list does not contain any key field (OK)
fields_high_null_perc = sold_full.columns[mask_high_null_perc]
# look into core fields
null_table.loc[['OriginalListPrice', 'ListPrice', 'ClosePrice', # 18 percent of records missing original list price (OK), 2 records missing close price
                'DaysOnMarket', # no records missing DOM (GOOD)
                'LivingArea']] # around 6 percent of records missing living area

# (ii) validate data types
# date fields
date_fields = ['ListingContractDate', 'PurchaseContractDate', 'CloseDate', 'ContractStatusChangeDate']
sold_full[date_fields] = sold_full[date_fields].apply(pd.to_datetime)
# numeric fields
numeric_fields = ['ClosePrice', 'OriginalListPrice', 'ListPrice', 'DaysOnMarket', 
                  'LivingArea', 'BedroomsTotal', 'BathroomsTotalInteger', 'LotSizeAcres', 'YearBuilt', 
                  'Latitude', 'Longitude', 
                  'rate_30yr_fixed']
sold_full[numeric_fields] = sold_full[numeric_fields].apply(pd.to_numeric)

# (iii) flag records with invalid date order
sold_full['listing_after_purchase_flag'] = sold_full['ListingContractDate'] > sold_full['PurchaseContractDate'] # 261 records
sold_full['listing_after_close_flag'] = sold_full['ListingContractDate'] > sold_full['CloseDate'] # 58 records
sold_full['purchase_after_close_flag'] = sold_full['PurchaseContractDate'] > sold_full['CloseDate'] # 240 records
sold_full['negative_timeline_flag'] = sold_full['listing_after_purchase_flag'] | sold_full['listing_after_close_flag'] | sold_full['purchase_after_close_flag'] # 501 records in total

# (iv) flag records with invalid numeric values
# inspect the distribution of numeric fields
sold_full[numeric_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # issues observed: abnormally high bedroom/bathroom counts; negative DOM, DOM over 32 years (to be verified); zero living area; properties built this year (to be verified)
                                                                            # list price vs original list price: original list price shows more variation though similar middle percentiles
# look into coordinates
sold_full['missing_coord_flag'] = sold_full['Latitude'].isna() | sold_full['Longitude'].isna() # 15822 records
sold_full['zero_coord_flag'] = (sold_full['Latitude'] == 0) | (sold_full['Longitude'] == 0) # 25 records
ca_lat = [32.5, 43]
ca_lon = [-124.26, -114.8]
sold_full['outside_ca_flag'] = (~sold_full['Longitude'].between(ca_lon[0], ca_lon[1])) | (~sold_full['Latitude'].between(ca_lat[0], ca_lat[1])) # 16279 records
# look into pricing
sold_full['missing_price_flag'] = sold_full['ClosePrice'].isna() # no records missing list price; 2 records
sold_full['invalid_price_flag'] = (sold_full['ListPrice'] <= 0) | (sold_full['ClosePrice'] <= 0) # original list price is not as important; 1 record
# look into time to sell
sold_full['negative_dom_flag'] = sold_full['DaysOnMarket'] < 0 # no records missing DOM; 46 records
# look into living space
sold_full['missing_living_space_flag'] = sold_full['LivingArea'].isna() # OK to miss bedroom or bathroom information; 229 records
sold_full['invalid_living_space_flag'] = (sold_full['LivingArea'] <= 0) | (sold_full['BedroomsTotal'] < 0) | (sold_full['BathroomsTotalInteger'] < 0) # 144records

sold_full.columns # confirm flags
sold_full.to_csv("raw-data/sold_residential_with_rates_flagged.csv", index=False)


"""
Part IV: Data Cleaning
"""

# (i) remove invalid records
mask_valid = ~(sold_full['negative_timeline_flag'] |
               sold_full['zero_coord_flag'] | sold_full['outside_ca_flag'] | 
               sold_full['invalid_price_flag'] | 
               sold_full['negative_dom_flag'] | 
               sold_full['invalid_living_space_flag'])
sold_valid = sold_full[mask_valid]
sold_valid.shape # 380718 records left

# (ii) remove outliers
# NOTE: percentiles are calculated for valid records ONLY
core_fields = ['ListPrice', 'ClosePrice', 'LivingArea', 'DaysOnMarket']
sold_valid[core_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])

q1 = sold_valid[core_fields].quantile(0.25)
q3 = sold_valid[core_fields].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
sold_valid['outlier_flag'] = ((sold_valid[core_fields] < lower) | (sold_valid[core_fields] > upper)).any(axis=1) # 60197 records
sold_reliable = sold_valid[~sold_valid['outlier_flag']]
sold_reliable.shape # 320521 records left
sold_reliable[core_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # mean and median decreased across the board

# (iii) remove records missing core values
mask_core_missing = ~(sold_reliable['missing_price_flag'] | 
                      sold_reliable['missing_living_space_flag']) # count is smaller than expected because some missing records have already been removed in the validation step
sold_core_not_missing = sold_reliable[mask_core_missing]
sold_core_not_missing.shape # 320422 records left
sold_core_not_missing.shape[0] / sold_full.shape[0] # around 80 percent of records retained

# (iv) remove unneeded fields
# fields with a significant amount of missing values
sold_clean = sold_core_not_missing.drop(columns=fields_high_null_perc)
sold_clean.shape[1] # 82 fields left
# flag fields
mask_flag = sold_clean.columns.str.endswith("_flag")
fields_flag = sold_clean.columns[mask_flag]
sold_clean = sold_clean.drop(columns=fields_flag)
sold_clean.shape[1] # 69 fields left

sold_clean.to_csv("clean-data/sold_residential_with_rates_clean.csv", index=False)