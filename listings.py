import pandas as pd

# TODO: establish a better workflow
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

listing_202601 = pd.read_csv('raw-data/CRMLSListing202601.csv')
listing_202602 = pd.read_csv('raw-data/CRMLSListing202602.csv')
listing_2026 = pd.concat([listing_202601, listing_202602])

listings = pd.concat([listing_2024, listing_2025, listing_2026])
listings.shape # (814871, 84)