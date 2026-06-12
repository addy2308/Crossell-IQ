import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib

# Load the Netflix feature matrix
df = pd.read_csv('data/feature_matrix.csv')

# Use the same features as the original segmentation
cluster_features = ['recency_days','frequency','monetary','tenure_days','num_products','engagement_score']
X = df[cluster_features].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4 clusters as before
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df['segment'] = kmeans.fit_predict(X_scaled)

# Map cluster IDs to meaningful names based on their characteristics
# We'll compute cluster centers to label them
centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=cluster_features)
centers['size'] = df['segment'].value_counts().sort_index().values
centers['avg_propensity'] = df.groupby('segment')['target'].mean().values * 100

# Assign names based on monetary value (higher = more valuable)
# 0 -> highest monetary -> High-Value Loyalist
# 3 -> lowest monetary -> Price-Sensitive
# The others accordingly
segment_names = {}
sorted_segments = centers.sort_values('monetary', ascending=False).index
names = ["High-Value Loyalist", "Dormant Upsell", "Life-Stage Triggered", "Price-Sensitive"]
for i, seg_id in enumerate(sorted_segments):
    segment_names[seg_id] = names[i]

df['segment_name'] = df['segment'].map(segment_names)

# Save updated feature matrix
df.to_csv('data/feature_matrix.csv', index=False)

# Also update customers.csv with segment info
cust = pd.read_csv('data/customers.csv')
cust = cust.merge(df[['customer_id', 'segment', 'segment_name']], on='customer_id', how='left')
cust.to_csv('data/customers.csv', index=False)

# Save the segmenter for later use
joblib.dump(kmeans, 'models/kprototypes.pkl')
print(f"Segments added. Distribution:\n{df['segment_name'].value_counts()}")
print(f"Segment names mapping: {segment_names}")
