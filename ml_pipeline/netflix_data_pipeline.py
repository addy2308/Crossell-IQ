"""
Optimized Netflix Data Pipeline
Efficiently loads and processes the Netflix Prize dataset with streaming/chunking.
Designed for 100M+ ratings dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Iterator, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetflixDataPipeline:
    """Handles efficient loading and processing of Netflix Prize data."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data' / 'netflix_prize'
        self.data_dir = Path(data_dir)
        self.processed_dir = Path(__file__).parent.parent / 'data' / 'processed'
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def load_movie_titles(self) -> pd.DataFrame:
        """Load movie titles and metadata."""
        movie_file = self.data_dir / 'movie_titles.csv'
        
        if not movie_file.exists():
            logger.warning(f"Movie titles file not found: {movie_file}")
            return pd.DataFrame()
        
        try:
            # movie_titles.csv format: movieID, year, title
            df = pd.read_csv(
                movie_file,
                header=None,
                names=['movie_id', 'year', 'title'],
                encoding='latin-1'
            )
            logger.info(f"Loaded {len(df)} movie titles")
            return df
        except Exception as e:
            logger.error(f"Error loading movie titles: {e}")
            return pd.DataFrame()
    
    def stream_ratings(self, chunk_size: int = 100000) -> Iterator[pd.DataFrame]:
        """
        Stream ratings from Netflix data files with chunking.
        Yields DataFrames of size chunk_size for memory efficiency.
        """
        required_files = [
            'combined_data_1.txt',
            'combined_data_2.txt',
            'combined_data_3.txt',
            'combined_data_4.txt'
        ]
        
        rows = []
        current_movie_id = None
        processed_count = 0
        
        for file_num, filename in enumerate(required_files, 1):
            filepath = self.data_dir / filename
            
            if not filepath.exists():
                logger.warning(f"File not found: {filepath}")
                continue
            
            logger.info(f"Processing {filename}... ({file_num}/4)")
            file_size_mb = filepath.stat().st_size / (1024**2)
            logger.info(f"  File size: {file_size_mb:.1f} MB")
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    if line.endswith(':'):
                        # Movie ID line
                        current_movie_id = int(line[:-1])
                    else:
                        # Rating line: user_id, rating, date
                        try:
                            parts = line.split(',')
                            if len(parts) == 3:
                                rows.append({
                                    'user_id': int(parts[0]),
                                    'movie_id': current_movie_id,
                                    'rating': int(parts[1]),
                                    'date': parts[2].strip()
                                })
                                processed_count += 1
                        except (ValueError, TypeError) as e:
                            if line_num % 1000000 == 0:
                                logger.debug(f"Skipped invalid line {line_num}: {e}")
                            continue
                    
                    # Yield chunk when size reached
                    if len(rows) >= chunk_size:
                        df = pd.DataFrame(rows)
                        df['date'] = pd.to_datetime(df['date'])
                        logger.info(f"  Yielding chunk: {len(rows)} ratings (total: {processed_count})")
                        yield df
                        rows = []
        
        # Yield remaining rows
        if rows:
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            logger.info(f"  Yielding final chunk: {len(rows)} ratings")
            yield df
        
        logger.info(f"Finished processing all files. Total: {processed_count} ratings")
    
    def aggregate_user_features(self) -> pd.DataFrame:
        """
        Aggregate user-level features from all ratings.
        This is the main feature engineering function.
        """
        logger.info("Aggregating user-level features...")
        
        user_features_list = []
        chunk_num = 0
        
        for chunk_df in self.stream_ratings():
            chunk_num += 1
            logger.info(f"Processing chunk {chunk_num}: {len(chunk_df)} ratings")
            
            # Aggregate ratings by user
            chunk_agg = chunk_df.groupby('user_id').agg({
                'movie_id': ['count', 'nunique'],  # frequency, diversity
                'rating': ['mean', 'std', 'min', 'max'],
                'date': ['min', 'max']
            }).reset_index()
            
            chunk_agg.columns = [
                'user_id',
                'total_ratings',
                'unique_movies',
                'mean_rating',
                'std_rating',
                'min_rating',
                'max_rating',
                'first_rating_date',
                'last_rating_date'
            ]
            
            user_features_list.append(chunk_agg)
        
        # Combine all chunks
        if not user_features_list:
            logger.error("No data loaded!")
            return pd.DataFrame()
        
        # Merge chunks and aggregate
        logger.info("Merging chunks...")
        combined = pd.concat(user_features_list, ignore_index=True)
        
        # Re-aggregate across all chunks for users appearing in multiple chunks
        user_agg = combined.groupby('user_id').agg({
            'total_ratings': 'sum',
            'unique_movies': 'sum',
            'mean_rating': 'mean',
            'std_rating': 'mean',
            'min_rating': 'min',
            'max_rating': 'max',
            'first_rating_date': 'min',
            'last_rating_date': 'max'
        }).reset_index()
        
        logger.info(f"Aggregated features for {len(user_agg)} unique users")
        return user_agg
    
    def calculate_temporal_features(self, user_agg: pd.DataFrame) -> pd.DataFrame:
        """Calculate time-based features."""
        logger.info("Calculating temporal features...")
        
        if user_agg.empty:
            return user_agg
        
        user_agg['first_rating_date'] = pd.to_datetime(user_agg['first_rating_date'])
        user_agg['last_rating_date'] = pd.to_datetime(user_agg['last_rating_date'])
        
        # Use the latest date in dataset as reference
        reference_date = user_agg['last_rating_date'].max()
        
        user_agg['tenure_days'] = (
            user_agg['last_rating_date'] - user_agg['first_rating_date']
        ).dt.days
        
        user_agg['recency_days'] = (
            reference_date - user_agg['last_rating_date']
        ).dt.days
        
        # Fill missing std_rating with mean
        user_agg['std_rating'] = user_agg['std_rating'].fillna(0)
        
        logger.info("Temporal features calculated")
        return user_agg
    
    def calculate_engagement_score(self, user_agg: pd.DataFrame) -> pd.DataFrame:
        """Calculate engagement and activity scores."""
        logger.info("Calculating engagement scores...")
        
        if user_agg.empty:
            return user_agg
        
        # Normalize features for scoring
        total_ratings = user_agg['total_ratings']
        tenure = user_agg['tenure_days'].clip(lower=1)
        recency = user_agg['recency_days']
        
        # Engagement: frequency per day (rating velocity)
        user_agg['rating_velocity'] = total_ratings / (tenure + 1)
        
        # Activity score: recent activity indicator
        user_agg['is_active_6m'] = (recency <= 180).astype(int)
        user_agg['is_active_1y'] = (recency <= 365).astype(int)
        
        # Rating consistency (lower std = more consistent)
        user_agg['rating_consistency'] = 1 / (1 + user_agg['std_rating'])
        
        # Engagement index (0-100)
        engagement_components = [
            total_ratings / total_ratings.max(),  # Frequency
            1 - (recency / recency.max()),  # Recency
            user_agg['mean_rating'] / 5,  # Satisfaction
            (tenure / tenure.max()).clip(0, 1)  # Loyalty
        ]
        user_agg['engagement_score'] = (
            np.mean(engagement_components, axis=0) * 100
        )
        
        logger.info("Engagement scores calculated")
        return user_agg
    
    def build_training_features(self) -> pd.DataFrame:
        """Build complete feature set for ML model."""
        logger.info("Building complete feature set...")
        
        # Aggregate user features
        user_agg = self.aggregate_user_features()
        
        if user_agg.empty:
            logger.error("No user aggregation data")
            return pd.DataFrame()
        
        # Calculate temporal features
        user_agg = self.calculate_temporal_features(user_agg)
        
        # Calculate engagement
        user_agg = self.calculate_engagement_score(user_agg)
        
        # Create cross-sell propensity target (synthetic for now)
        # Users with high engagement + recent activity = high propensity
        user_agg['cross_sell_propensity'] = (
            (user_agg['engagement_score'] / 100 * 0.4) +
            (user_agg['is_active_6m'] * 0.3) +
            (user_agg['rating_consistency'] * 0.3)
        )
        
        # Select final features
        feature_columns = [
            'user_id',
            'total_ratings',
            'unique_movies',
            'mean_rating',
            'std_rating',
            'min_rating',
            'max_rating',
            'tenure_days',
            'recency_days',
            'rating_velocity',
            'is_active_6m',
            'is_active_1y',
            'rating_consistency',
            'engagement_score',
            'cross_sell_propensity'
        ]
        
        features = user_agg[feature_columns].copy()
        features = features.fillna(0)
        
        logger.info(f"Built features for {len(features)} users")
        logger.info(f"Feature columns: {feature_columns}")
        
        return features
    
    def save_features(self, features: pd.DataFrame, name: str = 'netflix_features'):
        """Save features to disk."""
        output_path = self.processed_dir / f'{name}.parquet'
        features.to_parquet(output_path, index=False)
        logger.info(f"Features saved to {output_path} ({len(features)} rows)")
        return output_path


def main():
    """Run the complete pipeline."""
    pipeline = NetflixDataPipeline()
    
    # Build features
    features = pipeline.build_training_features()
    
    if not features.empty:
        # Save features
        pipeline.save_features(features)
        
        # Print summary
        print("\n" + "="*60)
        print("NETFLIX DATA PIPELINE SUMMARY")
        print("="*60)
        print(f"Total Users: {len(features)}")
        print(f"\nFeature Statistics:")
        print(features.describe())
        
        return True
    else:
        logger.error("Pipeline failed: no features generated")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
