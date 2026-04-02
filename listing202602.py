import pandas as pd

df = pd.read_csv('raw-data/CRMLSListing202602.csv')

# inspect all fields to understand basic listing structure
df.head()
df.shape # 32334 x 81
# fields fall into a few categories:
#   pricing: original list price, list price, close price
#   location: latitude and longitude, city, elementary school district, postal code, etc.
#   property details: property type, property subtype; living area, above grade finished area, below grade finished area, covered spaces, stories, building area total, lot size acres, bathrooms total integer; year built; etc.
#   time to sell: days on market
df.columns
# close date does not have consistent formatting
df.describe(include='all')

# remove irrelevant fields
df.columns
identifier_columns = ['ListingKey', 'ListingId', 'ListingKeyNumeric']
redundant_columns = [col for col in df.columns if col.endswith('.1')] # 11 fields have largely duplicated data (e.g., LivingArea.1 has 27977 duplicates vs 4357 unique values) 
df_clean = df.drop(columns=redundant_columns + identifier_columns)
len(df_clean.columns) # 67 fields left

# standardize date fields
date_columns = [col for col in df_clean.columns if 'Date' in col]
date_columns
# first convert close date to datetime
df_clean[date_columns[0]].isna().sum() # most of the close dates are missing (24777 in 32334) (OK)
closed_listings = df_clean[date_columns[0]].notna() # mask for filtering
df_clean[closed_listings][date_columns[0]] = pd.to_datetime(df_clean[closed_listings][date_columns[0]]) # TODO: set with copy warning
# then contract status change date
df_clean[date_columns[1]].isna().sum() # 315 change dates missing (OK)
changed_listings = df_clean[date_columns[1]].notna()
df_clean[changed_listings][date_columns[1]] = pd.to_datetime(df_clean[changed_listings][date_columns[1]]) # TODO: set with copy warning
# then purchase contract date
df_clean[date_columns[2]].isna().sum() # 18731 listings not yet purchased
purchased_listings = df_clean[date_columns[2]].notna()
df_clean[purchased_listings][date_columns[2]] = pd.to_datetime(df_clean[purchased_listings][date_columns[2]]) # TODO: set with copy warning
# then listing contract date
df_clean[date_columns[-1]].isna().sum() # all listings have established proper contracts between seller and seller's broker, no missing values
df_clean[date_columns[-1]] = pd.to_datetime(df_clean[date_columns[-1]])
# take a final look
df_clean[date_columns]