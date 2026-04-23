import numpy as np
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
Part III: Validate data
"""

sold_full = pd.read_csv('raw-data/sold_residential_with_rates_raw.csv')
sold_full['MlsStatus'].unique() # confirm that all transactions are indeed closed
sold_full = sold_full.replace(r'^\s*$', np.nan, regex=True) # convert blank strings to NaN to ensure they are handled as missing values

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
null_table.loc[['OriginalListPrice', 'ListPrice', 'ClosePrice', # 18 percent of records missing original list price, 2 records missing close price
                'DaysOnMarket', 
                'LivingArea', # 6 percent of records missing living area
                'CloseDate', 'PurchaseContractDate', 'ListingContractDate']] # 5 percent missing purchase date, 1 record missing listing date

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

# (iii) flag records with invalid dates
# unreasonable date order
sold_full['listing_after_purchase_flag'] = sold_full['ListingContractDate'] > sold_full['PurchaseContractDate'] # 261 records
sold_full['listing_after_close_flag'] = sold_full['ListingContractDate'] > sold_full['CloseDate'] # 58 records
sold_full['purchase_after_close_flag'] = sold_full['PurchaseContractDate'] > sold_full['CloseDate'] # 240 records
sold_full['negative_timeline_flag'] = sold_full['listing_after_purchase_flag'] | sold_full['listing_after_close_flag'] | sold_full['purchase_after_close_flag'] # 501 records in total
# date missing
sold_full['missing_listing_date_flag'] = sold_full['ListingContractDate'].isna() # 1 record
sold_full['missing_purchase_date_flag'] = sold_full['PurchaseContractDate'].isna() # 194 records

# (iv) flag records with invalid numeric values
# inspect the distribution of numeric fields
sold_full[numeric_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # issues observed: close price as zero, original list price as zero; abnormally high bedroom/bathroom counts; negative DOM, DOM over 32 years; zero living area; most recently sold properties were built this year
                                                                            # original list price shows more variation though similar middle percentiles compared to list price
# look into coordinates
sold_full['missing_coord_flag'] = sold_full['Latitude'].isna() | sold_full['Longitude'].isna() # 15822 records
sold_full['zero_coord_flag'] = (sold_full['Latitude'] == 0) | (sold_full['Longitude'] == 0) # 25 records
ca_lat = [32.5, 43]
ca_lon = [-124.26, -114.8]
sold_full['outside_ca_flag'] = (~sold_full['Longitude'].between(ca_lon[0], ca_lon[1])) | (~sold_full['Latitude'].between(ca_lat[0], ca_lat[1])) # 16279 records
# look into pricing
sold_full['missing_original_list_price_flag'] = sold_full['OriginalListPrice'].isna() # 721 records
sold_full['missing_close_price_flag'] = sold_full['ClosePrice'].isna() # 2 records
sold_full['invalid_price_flag'] = (sold_full['OriginalListPrice'] <= 0) | (sold_full['ListPrice'] <= 0) | (sold_full['ClosePrice'] <= 0) # 3 records
# look into time to sell
sold_full['negative_dom_flag'] = sold_full['DaysOnMarket'] < 0 # 46 records
# look into living space
sold_full['missing_living_space_flag'] = sold_full['LivingArea'].isna() # OK to miss bedroom or bathroom information; 229 records
sold_full['invalid_living_space_flag'] = (sold_full['LivingArea'] <= 0) | (sold_full['BedroomsTotal'] < 0) | (sold_full['BathroomsTotalInteger'] < 0) # 144 records

sold_full.columns # confirm flags
sold_full.to_csv("raw-data/sold_residential_with_rates_flagged.csv", index=False)


"""
Part IV: Clean data
"""

# (i) remove invalid records
mask_valid = ~(sold_full['negative_timeline_flag'] |
               sold_full['zero_coord_flag'] | sold_full['outside_ca_flag'] | 
               sold_full['invalid_price_flag'] | 
               sold_full['negative_dom_flag'] | 
               sold_full['invalid_living_space_flag'])
sold_valid = sold_full[mask_valid]
sold_valid.shape # 380716 records left

# (ii) remove outliers
# NOTE: percentiles are calculated on valid records ONLY
core_fields = ['OriginalListPrice', 'ClosePrice', 'LivingArea', 'DaysOnMarket']
sold_valid[core_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])

q1 = sold_valid[core_fields].quantile(0.25)
q3 = sold_valid[core_fields].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
sold_valid['outlier_flag'] = ((sold_valid[core_fields] < lower) | (sold_valid[core_fields] > upper)).any(axis=1) # 60693 records
sold_reliable = sold_valid[~sold_valid['outlier_flag']]
sold_reliable.shape # 320023 records left
sold_reliable[core_fields].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # mean and median have gone down considerably across all core fields

# (iii) remove records missing core values
mask_core_missing = (sold_reliable['missing_original_list_price_flag'] | sold_reliable['missing_close_price_flag'] | 
                     sold_reliable['missing_listing_date_flag'] | sold_reliable['missing_purchase_date_flag'] | 
                     sold_reliable['missing_living_space_flag']) # count is smaller than expected because some missing records have already been removed in previous steps
sold_core_not_missing = sold_reliable[~mask_core_missing]
sold_core_not_missing.shape # 319480 records left
sold_core_not_missing.shape[0] / sold_full.shape[0] # 80 percent of records retained

# (iv) remove unneeded fields
# fields with a significant amount of missing values
sold_clean = sold_core_not_missing.drop(columns=fields_high_null_perc)
sold_clean.shape[1] # 85 fields left
# flag fields
mask_flag = sold_clean.columns.str.endswith("_flag")
fields_flag = sold_clean.columns[mask_flag]
sold_clean = sold_clean.drop(columns=fields_flag)
sold_clean.shape[1] # 69 fields left

sold_clean.to_csv("clean-data/sold_residential_with_rates_clean.csv", index=False)


"""
Part V: Compute market metrics
"""

# metrics related to price
sold_clean['price_ratio'] = sold_clean['ClosePrice'] / sold_clean['OriginalListPrice']
sold_clean['close_to_original_list_ratio'] = sold_clean['ClosePrice'] / sold_clean['OriginalListPrice']
sold_clean['price_per_sq_ft'] = sold_clean['ClosePrice'] / sold_clean['LivingArea']
price_metrics = ['price_ratio', 'close_to_original_list_ratio', 'price_per_sq_ft']

# metrics related to time to sell
sold_clean['days_on_market'] = sold_clean['DaysOnMarket'] # differentiate metric from data field
sold_clean['listing_to_contract'] = (sold_clean['PurchaseContractDate'] - sold_clean['ListingContractDate']).dt.days
sold_clean['contract_to_close'] = (sold_clean['CloseDate'] - sold_clean['PurchaseContractDate']).dt.days
time_metrics = ['days_on_market', 'listing_to_contract', 'contract_to_close']

# metrics related to close date
sold_clean['close_year'] = sold_clean['CloseDate'].dt.year
sold_clean['close_month'] = sold_clean['CloseDate'].dt.month
sold_clean['close_year_month'] = sold_clean['year_month'] # recall that mortgage rates are merged based on a year-month key derived from close date
sold_clean['close_yrmo'] = sold_clean['CloseDate'].dt.strftime("%y%m") # year month in alternative format
close_metrics = ['close_year', 'close_month']


"""
Part VI: Analyze market metrics 
"""

# (i) overall
sold_clean[price_metrics].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # price ratio tends to be close to 1 (healthy market)
sold_clean[time_metrics].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]) # property listed, contract signed, and deal closed can all happen in as short as one day
                                                                           # contract to close typically takes shorter than listing to contract
                                                                           # NOTE: max DOM is considerably shorter than max listing to contracy
sold_clean[close_metrics[0]].value_counts() # 2024 has the most sales so far
sold_clean[close_metrics[1]].value_counts() # March has the most sales so far, followed by May and July
                                            # winter months seem to have fewer sales
                                            # keep in mind that we don't have data from the rest of 2026 yet

# (ii) by property type
sold_clean['PropertyType'].unique() # recall that we've fitered for residential transactions
sold_clean['PropertySubType'].unique() # 20 subtypes: single family residence (i.e. SFR, the benchmark); condominium (i.e. condo); townhouse; manufactured on land, manufactured home, stock cooperative (residents buy shares in the housing corporation); duplex, triplex, quadruplex, loft, studio (often multi-family); other types including mobile home, mixed use, boat slip (single-boat parking space at a dock), farm, co-ownership, deeded parking (parking space with a legal deed), own your own (i.e. OYO, residents hold exclusive rights to the unit), cabin, time share (vacation property owned and used by multiple buyers during specific periods); have several NaNs
core_subtypes = sold_clean['PropertySubType'].value_counts().head(6).index # focus on subtypes with the most sales (for now)
# price
sold_clean.groupby('PropertySubType')[price_metrics[0]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_subtypes] # NOTE: variation in SFR, condo, and townhouse is heavily inflated by outliers
                                                                                                                             # SFRs have higher price ratio than most of the other subtypes
sold_clean.groupby('PropertySubType')[price_metrics[2]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_subtypes] # townhouses and condos have higher unit price than SFRs; manufactured homes are the cheapest in terms of unit price
# time to sell
sold_clean.groupby('PropertySubType')[time_metrics[0]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_subtypes] # condos and manufactured take longer to sell; SFRs move through the sale cycle the fastest  
sold_clean.groupby('PropertySubType')[time_metrics[1]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_subtypes] # SFRs and townhouses take shorter to reach accepted offer
sold_clean.groupby('PropertySubType')[time_metrics[2]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_subtypes] # stock co-ops have considerably longer average escrow period
# close date
sold_clean.groupby('PropertySubType')[close_metrics[0]].value_counts().loc[core_subtypes] # all subtypes have relatively more sales in 2024 than 2025
sold_clean.groupby('PropertySubType')[close_metrics[1]].value_counts().loc[core_subtypes] # sales peaks for each subtype occur in different months

# (iii) by region
# county or parish
sold_clean['CountyOrParish'].unique() # 59 counties/parishes
core_county_or_parish = sold_clean['CountyOrParish'].value_counts().head(9).index # focus on counties/parishes with the most sales (for now)
# price
sold_clean.groupby('CountyOrParish')[price_metrics[0]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_county_or_parish]
sold_clean.groupby('CountyOrParish')[price_metrics[2]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_county_or_parish] # Santa Clara has the highest unit price, not Los Angeles!
# time to sell
sold_clean.groupby('CountyOrParish')[time_metrics[0]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_county_or_parish] # Santa Clara also moves through the sale cycle the fastest
sold_clean.groupby('CountyOrParish')[time_metrics[1]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_county_or_parish]
sold_clean.groupby('CountyOrParish')[time_metrics[2]].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).loc[core_county_or_parish]
# close date
sold_clean.groupby('CountyOrParish')[close_metrics[1]].value_counts().loc[core_county_or_parish]

# TODO: major marketing area defined by the MLS
sold_clean['MLSAreaMajor'].unique() # 1067 areas (more granular than government defined regions)
sold_clean['MLSAreaMajor'].value_counts() # many undefined records
                                          # southwest riverside county has the most sales

# (iv) by agent
# TODO: list office
sold_clean['ListOfficeName'].unique() # 16934 list agents
# TODO: buyer office
sold_clean['BuyerOfficeName'].unique() # 19241 buyer agents