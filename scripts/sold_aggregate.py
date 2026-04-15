import numpy as np
import pandas as pd

# aggregate all monthly sold transactions in the 2024 calendar year
sold_202401 = pd.read_csv('raw-data/CRMLSSold202401.csv')
sold_202402 = pd.read_csv('raw-data/CRMLSSold202402.csv')
sold_202403 = pd.read_csv('raw-data/CRMLSSold202403.csv')
sold_202404 = pd.read_csv('raw-data/CRMLSSold202404.csv') # NOTE: mixed types in columns 2, 36, 39, 56, 74
sold_202405 = pd.read_csv('raw-data/CRMLSSold202405.csv')
sold_202406 = pd.read_csv('raw-data/CRMLSSold202406.csv')
sold_202407 = pd.read_csv('raw-data/CRMLSSold202407.csv')
sold_202408 = pd.read_csv('raw-data/CRMLSSold202408.csv')
sold_202409 = pd.read_csv('raw-data/CRMLSSold202409.csv')
sold_202410 = pd.read_csv('raw-data/CRMLSSold202410.csv')
sold_202411 = pd.read_csv('raw-data/CRMLSSold202411.csv')
sold_202412 = pd.read_csv('raw-data/CRMLSSold202412.csv')
sold_2024 = pd.concat([sold_202401, sold_202402, sold_202403, sold_202404, 
                       sold_202405, sold_202406, sold_202407, sold_202408,
                       sold_202409, sold_202410, sold_202411, sold_202412])
sold_2024.shape # (272491, 84)

# aggregate all monthly sold transactions in the 2025 calendar year
sold_202501 = pd.read_csv('raw-data/CRMLSSold202501.csv')
sold_202502 = pd.read_csv('raw-data/CRMLSSold202502.csv')
sold_202503 = pd.read_csv('raw-data/CRMLSSold202503.csv')
sold_202504 = pd.read_csv('raw-data/CRMLSSold202504.csv')
sold_202505 = pd.read_csv('raw-data/CRMLSSold202505.csv')
sold_202506 = pd.read_csv('raw-data/CRMLSSold202506.csv') # NOTE: mixed types in column 4
sold_202507 = pd.read_csv('raw-data/CRMLSSold202507.csv')
sold_202508 = pd.read_csv('raw-data/CRMLSSold202508.csv')
sold_202509 = pd.read_csv('raw-data/CRMLSSold202509.csv')
sold_202510 = pd.read_csv('raw-data/CRMLSSold202510.csv')
sold_202511 = pd.read_csv('raw-data/CRMLSSold202511.csv')
sold_202512 = pd.read_csv('raw-data/CRMLSSold202512.csv')
sold_2025 = pd.concat([sold_202501, sold_202502, sold_202503, sold_202504, 
                       sold_202505, sold_202506, sold_202507, sold_202508,
                       sold_202509, sold_202510, sold_202511, sold_202512])
sold_2025.shape # (260104, 80)
                # NOTE: 2025 field count does not match 2024 field count

# aggregate all monthly sold transactions in the 2026 calendar year (up to March)
sold_202601 = pd.read_csv('raw-data/CRMLSSold202601.csv') # NOTE: mixed types in columns 4, 74
sold_202602 = pd.read_csv('raw-data/CRMLSSold202602.csv')
sold_202603 = pd.read_csv('raw-data/CRMLSSold202603.csv')
sold_2026 = pd.concat([sold_202601, sold_202602, sold_202603])
sold_2026.shape # (59138, 80)
                # NOTE: 2026 field count does not match 2024 field count

# investigate field discrepancy
np.sum(sold_2025.columns == sold_2026.columns) # 2 fields do not match
sold_2025.columns[sold_2025.columns != sold_2026.columns] # lat filled and lon filled for the 2025 dataset
sold_2026.columns[sold_2025.columns != sold_2026.columns] # originating system name and originating system sub name for the 2026 dataset
set(sold_2024.columns) - set(sold_2025.columns) # 2024 dataset includes the two misaligned fields from the 2026 dataset as well as buyer agency compensation and buyer agency compensation type
set(sold_2024.columns) - set(sold_2026.columns) # 2024 dataset also includes the two misaligned fields from the 2025 dataset (looks like the 2024 dataset is all-encompassing)

# aggregate all monthly sold transactions across the three calendar years
sold = pd.concat([sold_2024, sold_2025, sold_2026]) # aggregate by field names
sold.shape # (591733, 84)
sold.columns # verify that the full dataset contains all fields

sold.to_csv("raw-data/sold_raw.csv", index=False)