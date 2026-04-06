import numpy as np
import pandas as pd

# aggregate all monthly listings in the 2024 calendar year
listing_202401 = pd.read_csv('raw-data/CRMLSListing202401.csv')
listing_202402 = pd.read_csv('raw-data/CRMLSListing202402.csv')
listing_202403 = pd.read_csv('raw-data/CRMLSListing202403.csv')
listing_202404 = pd.read_csv('raw-data/CRMLSListing202404.csv')
listing_202405 = pd.read_csv('raw-data/CRMLSListing202405.csv')
listing_202406 = pd.read_csv('raw-data/CRMLSListing202406.csv')
listing_202407 = pd.read_csv('raw-data/CRMLSListing202407.csv')
listing_202408 = pd.read_csv('raw-data/CRMLSListing202408.csv')
listing_202409 = pd.read_csv('raw-data/CRMLSListing202409.csv')
listing_202410 = pd.read_csv('raw-data/CRMLSListing202410.csv')
listing_202411 = pd.read_csv('raw-data/CRMLSListing202411.csv')
listing_202412 = pd.read_csv('raw-data/CRMLSListing202412.csv')
listing_2024 = pd.concat([listing_202401, listing_202402, listing_202403, listing_202404, 
                          listing_202405, listing_202406, listing_202407, listing_202408, 
                          listing_202409, listing_202410, listing_202411, listing_202412])
listing_2024.shape # (383920, 84)

# aggregate all monthly listings in the 2025 calendar year
listing_202501 = pd.read_csv('raw-data/CRMLSListing202501.csv')
listing_202502 = pd.read_csv('raw-data/CRMLSListing202502.csv')
listing_202503 = pd.read_csv('raw-data/CRMLSListing202503.csv')
listing_202504 = pd.read_csv('raw-data/CRMLSListing202504.csv')
listing_202505 = pd.read_csv('raw-data/CRMLSListing202505.csv')
listing_202506 = pd.read_csv('raw-data/CRMLSListing202506.csv')
listing_202507 = pd.read_csv('raw-data/CRMLSListing202507.csv')
listing_202508 = pd.read_csv('raw-data/CRMLSListing202508.csv')
listing_202509 = pd.read_csv('raw-data/CRMLSListing202509.csv')
listing_202510 = pd.read_csv('raw-data/CRMLSListing202510.csv')
listing_202511 = pd.read_csv('raw-data/CRMLSListing202511.csv')
listing_202512 = pd.read_csv('raw-data/CRMLSListing202512.csv')
listing_2025 = pd.concat([listing_202501, listing_202502, listing_202503, listing_202504, 
                          listing_202505, listing_202506, listing_202507, listing_202508, 
                          listing_202509, listing_202510, listing_202511, listing_202512])
listing_2025.shape # (363315, 82) 
                   # NOTE: 2025 field count does not match 2024 field count

# aggregate all monthly listings in the 2026 calendar year (up to March)
listing_202601 = pd.read_csv('raw-data/CRMLSListing202601.csv')
listing_202602 = pd.read_csv('raw-data/CRMLSListing202602.csv')
listing_202603 = pd.read_csv('raw-data/CRMLSListing202603.csv')
listing_2026 = pd.concat([listing_202601, listing_202602, listing_202603])
listing_2026.shape # (106744, 82)
                   # NOTE: 2026 field count does not match 2024 field count

# investigate field discrepancy
np.sum(listing_2025.columns == listing_2026.columns) # 2025 and 2026 fields match exactly, so we can use either the 2025 or 2026 listing data to continue troubleshooting
set(listing_2024.columns) - set(listing_2025.columns) # 2025 and 2026 listing data do not include buyer agency compensation and buyer agency compensation type

# aggregate all monthly listings across the three calendar years
listings = pd.concat([listing_2024, listing_2025, listing_2026]) # aggregate by field names
listings.shape # (853979, 84)
listings['BuyerAgencyCompensation'][listing_2024.shape[0]:] # 2025 and 2026 records treat buyer agency compensation and buyer agency compensation type as missing (OK)
listings['BuyerAgencyCompensationType'][listing_2024.shape[0]:]

listings.to_csv("raw-data/listings_raw.csv", index=False)