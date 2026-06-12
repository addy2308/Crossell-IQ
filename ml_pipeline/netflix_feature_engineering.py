"""
Advanced Feature Engineering for Netflix Cross-Sell Model
Extracts genre preferences, user segments, and cross-sell indicators.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetflixFeatureEngineer:
    """Advanced feature engineering for Netflix cross-sell propensity."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data' / 'netflix_prize'
        self.data_dir = Path(data_dir)
        self.movie_metadata = self._load_movie_metadata()
    
    def _load_movie_metadata(self) -> pd.DataFrame:
        """Load movie titles and extract metadata."""
        movie_file = self.data_dir / 'movie_titles.csv'
        
        if not movie_file.exists():
            logger.warning(f"Movie file not found: {movie_file}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(
                movie_file,
                header=None,
                names=['movie_id', 'year', 'title'],
                encoding='latin-1'
            )
            
            # Extract simple genres from title (heuristic-based)
            df['genre_action'] = df['title'].str.contains(
                r'action|fight|war|battle|shoot|gun|spy|hero', 
                case=False, regex=True
            ).astype(int)
            df['genre_drama'] = df['title'].str.contains(
                r'drama|family|story|life', 
                case=False, regex=True
            ).astype(int)
            df['genre_comedy'] = df['title'].str.contains(
                r'comedy|funny|laugh|comic', 
                case=False, regex=True
            ).astype(int)
            df['genre_scifi'] = df['title'].str.contains(
                r'scifi|sci-fi|future|space|aliens|robot|matrix', 
                case=False, regex=True
            ).astype(int)
            df['genre_horror'] = df['title'].str.contains(
                r'horror|scary|evil|ghost|killer|dark|terror', 
                case=False, regex=True
            ).astype(int)
            
            logger.info(f"Loaded metadata for {len(df)} movies")
            return df
        
        except Exception as e:
            logger.error(f"Error loading movie metadata: {e}")
            return pd.DataFrame()
    
    def engineer_genre_preferences(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer genre preference features for each user.
        
        Args:
            ratings_df: DataFrame with columns [user_id, movie_id, rating, date]
        
        Returns:
            DataFrame with user genre preference features
        """
        logger.info("Engineering genre preferences...")
        
        if self.movie_metadata.empty:
            logger.warning("No movie metadata available for genre analysis")
            return ratings_df.groupby('user_id').size().reset_index(name='total_ratings')
        
        # Merge ratings with movie metadata
        merged = ratings_df.merge(
            self.movie_metadata[['movie_id', 'genre_action', 'genre_drama', 
                                 'genre_comedy', 'genre_scifi', 'genre_horror']],
            on='movie_id',
            how='left'
        )
        
        # For each genre, calculate user preferences
        genre_cols = ['genre_action', 'genre_drama', 'genre_comedy', 
                      'genre_scifi', 'genre_horror']
        
        user_genres = {}
        
        for genre in genre_cols:
            genre_name = genre.replace('genre_', '')
            
            # Calculate average rating for this genre
            genre_ratings = merged[merged[genre] == 1].groupby('user_id').agg({
                'rating': ['mean', 'count']
            }).reset_index()
            
            genre_ratings.columns = ['user_id', f'{genre_name}_avg_rating', f'{genre_name}_count']
            user_genres[genre_name] = genre_ratings
        
        # Combine all genre features
        user_genre_features = ratings_df.groupby('user_id').size().reset_index(name='total_ratings')
        
        for genre_name, genre_df in user_genres.items():
            user_genre_features = user_genre_features.merge(
                genre_df,
                on='user_id',
                how='left'
            )
        
        # Fill NaN with 0 for genres user hasn't rated
        for col in user_genre_features.columns:
            if col != 'user_id':
                user_genre_features[col] = user_genre_features[col].fillna(0)
        
        # Normalize genre preferences (0-100 scale)
        for genre in ['action', 'drama', 'comedy', 'scifi', 'horror']:
            avg_col = f'{genre}_avg_rating'
            if avg_col in user_genre_features.columns:
                user_genre_features[f'{genre}_preference'] = (
                    user_genre_features[avg_col] / 5 * 100
                )
        
        logger.info(f"Genre features computed for {len(user_genre_features)} users")
        return user_genre_features
    
    def engineer_rating_distribution_features(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from rating distributions.
        Users who rate consistently high vs low indicate different propensities.
        """
        logger.info("Engineering rating distribution features...")
        
        rating_dist = ratings_df.groupby('user_id').agg({
            'rating': [
                ('rating_5star_pct', lambda x: (x == 5).sum() / len(x) * 100),
                ('rating_4star_pct', lambda x: (x == 4).sum() / len(x) * 100),
                ('rating_3star_pct', lambda x: (x == 3).sum() / len(x) * 100),
                ('rating_12star_pct', lambda x: (x < 3).sum() / len(x) * 100),
                ('rating_variance', 'var'),
                ('rating_skew', lambda x: pd.Series(x).skew())
            ]
        }).reset_index()
        
        rating_dist.columns = ['user_id', 'rating_5star_pct', 'rating_4star_pct',
                               'rating_3star_pct', 'rating_12star_pct',
                               'rating_variance', 'rating_skew']
        
        # Fill NaN
        rating_dist = rating_dist.fillna(0)
        
        logger.info(f"Rating distribution features for {len(rating_dist)} users")
        return rating_dist
    
    def engineer_temporal_segments(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Segment users by temporal activity patterns.
        Identifies early adopters, seasonal users, consistent users, etc.
        """
        logger.info("Engineering temporal segments...")
        
        ratings_df['date'] = pd.to_datetime(ratings_df['date'])
        reference_date = ratings_df['date'].max()
        
        # Calculate activity by year
        ratings_df['year'] = ratings_df['date'].dt.year
        
        yearly_activity = ratings_df.groupby(['user_id', 'year']).size().reset_index(name='count')
        pivot_activity = yearly_activity.pivot(index='user_id', columns='year', values='count').fillna(0)
        pivot_activity = pivot_activity.reset_index()
        pivot_activity.columns.name = None
        
        # Calculate growth trend
        if len(pivot_activity.columns) > 2:
            years = sorted([c for c in pivot_activity.columns if isinstance(c, (int, float))])
            if len(years) >= 2:
                pivot_activity['trend_growth'] = (
                    (pivot_activity[years[-1]] - pivot_activity[years[0]]) / 
                    (pivot_activity[years[0]] + 1) * 100
                )
        else:
            pivot_activity['trend_growth'] = 0
        
        # Identify user segments
        total_ratings = ratings_df.groupby('user_id').size().reset_index(name='total_ratings')
        pivot_activity = pivot_activity.merge(total_ratings, on='user_id')
        
        pivot_activity['is_early_adopter'] = (
            (ratings_df.groupby('user_id')['date'].min() <= '2000-12-31').map(
                ratings_df.groupby('user_id')['date'].min()
            )
        ).astype(int)
        
        logger.info(f"Temporal segments for {len(pivot_activity)} users")
        return pivot_activity
    
    def engineer_cross_sell_readiness_score(self, user_features: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate cross-sell readiness score based on multiple factors.
        Higher score = more likely to accept cross-sell offer.
        """
        logger.info("Calculating cross-sell readiness scores...")
        
        df = user_features.copy()
        
        # Component scores (0-1 scale)
        scores = []
        
        # 1. Engagement level (frequency + recent activity)
        if 'total_ratings' in df.columns:
            engagement = df['total_ratings'] / df['total_ratings'].max()
            scores.append(('engagement', engagement, 0.25))
        
        # 2. Recency (active recently)
        if 'recency_days' in df.columns:
            recency_score = 1 - (df['recency_days'] / (df['recency_days'].max() + 1))
            recency_score = recency_score.clip(0, 1)
            scores.append(('recency', recency_score, 0.25))
        
        # 3. Satisfaction (high average ratings)
        if 'mean_rating' in df.columns:
            satisfaction = df['mean_rating'] / 5
            scores.append(('satisfaction', satisfaction, 0.20))
        
        # 4. Genre diversity (interest in multiple genres)
        genre_cols = [c for c in df.columns if 'preference' in c]
        if genre_cols:
            # Count how many genres user has rated
            genre_interest = (df[genre_cols] > 0).sum(axis=1) / len(genre_cols)
            scores.append(('diversity', genre_interest, 0.15))
        
        # 5. Loyalty (tenure)
        if 'tenure_days' in df.columns:
            loyalty = df['tenure_days'] / (df['tenure_days'].max() + 1)
            loyalty = loyalty.clip(0, 1)
            scores.append(('loyalty', loyalty, 0.15))
        
        # Combine weighted scores
        cross_sell_score = pd.Series(0.0, index=df.index)
        
        for name, score, weight in scores:
            cross_sell_score += (score * weight)
        
        df['cross_sell_readiness'] = cross_sell_score * 100  # Scale to 0-100
        
        # Segment users
        df['crosssell_segment'] = pd.cut(
            df['cross_sell_readiness'],
            bins=[0, 25, 50, 75, 100],
            labels=['Low', 'Medium', 'High', 'Very High']
        )
        
        logger.info(f"Cross-sell readiness scores calculated for {len(df)} users")
        logger.info(f"Segment distribution:\n{df['crosssell_segment'].value_counts().sort_index()}")
        
        return df


def main():
    """Run feature engineering pipeline."""
    engineer = NetflixFeatureEngineer()
    print("\nFeature Engineering Module Ready")
    print("="*60)
    print("Use NetflixFeatureEngineer to extract advanced features:")
    print("  - Genre preferences")
    print("  - Rating distributions")
    print("  - Temporal segments")
    print("  - Cross-sell readiness scores")


if __name__ == '__main__':
    main()
