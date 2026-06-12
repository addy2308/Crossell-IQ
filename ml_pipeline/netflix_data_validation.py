"""
Data Validation and Quality Checks for Netflix Dataset
Validates dataset completeness, quality, and consistency.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetflixDataValidator:
    """Validates Netflix dataset quality and completeness."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data' / 'netflix_prize'
        self.data_dir = Path(data_dir)
        self.validation_report = {}
    
    def check_files_exist(self) -> Dict[str, bool]:
        """Check if all required dataset files exist."""
        required_files = {
            'combined_data_1.txt': 'Netflix ratings part 1',
            'combined_data_2.txt': 'Netflix ratings part 2',
            'combined_data_3.txt': 'Netflix ratings part 3',
            'combined_data_4.txt': 'Netflix ratings part 4',
            'movie_titles.csv': 'Movie metadata'
        }
        
        logger.info("Checking for required files...")
        results = {}
        
        for filename, description in required_files.items():
            filepath = self.data_dir / filename
            exists = filepath.exists()
            results[filename] = exists
            
            if exists:
                size_mb = filepath.stat().st_size / (1024**2)
                logger.info(f"  ✓ {filename} ({size_mb:.1f} MB)")
            else:
                logger.warning(f"  ✗ {filename} - MISSING")
        
        self.validation_report['files_exist'] = results
        return results
    
    def check_movie_titles_format(self) -> Dict[str, any]:
        """Validate movie_titles.csv format."""
        logger.info("Validating movie_titles.csv format...")
        
        movie_file = self.data_dir / 'movie_titles.csv'
        results = {
            'valid': False,
            'total_movies': 0,
            'issues': []
        }
        
        if not movie_file.exists():
            results['issues'].append('File not found')
            return results
        
        try:
            df = pd.read_csv(
                movie_file,
                header=None,
                names=['movie_id', 'year', 'title'],
                encoding='latin-1'
            )
            
            # Check structure
            if len(df.columns) != 3:
                results['issues'].append(f'Expected 3 columns, got {len(df.columns)}')
            
            # Check movie_id is numeric
            if not pd.api.types.is_integer_dtype(df['movie_id']):
                results['issues'].append('movie_id is not numeric')
            
            # Check year is valid
            invalid_years = df[(df['year'] < 1000) | (df['year'] > 2006)]['year'].unique()
            if len(invalid_years) > 0:
                results['issues'].append(
                    f'Invalid years found: {len(invalid_years)} anomalies'
                )
            
            results['total_movies'] = len(df)
            results['valid'] = len(results['issues']) == 0
            
            logger.info(f"  Movies: {len(df)}")
            logger.info(f"  Year range: {df['year'].min()}-{df['year'].max()}")
            logger.info(f"  Valid: {results['valid']}")
            
        except Exception as e:
            results['issues'].append(str(e))
            logger.error(f"  Error: {e}")
        
        self.validation_report['movie_titles'] = results
        return results
    
    def sample_ratings_format(self, sample_lines: int = 1000) -> Dict[str, any]:
        """Sample and validate ratings file format."""
        logger.info(f"Sampling ratings format ({sample_lines} lines)...")
        
        results = {
            'valid': False,
            'total_sampled': 0,
            'valid_ratings': 0,
            'movie_ids_found': set(),
            'rating_range': (0, 0),
            'issues': []
        }
        
        required_files = ['combined_data_1.txt', 'combined_data_2.txt']
        
        for filename in required_files:
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue
            
            current_movie_id = None
            valid_count = 0
            total_count = 0
            ratings = []
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= sample_lines:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    total_count += 1
                    
                    if line.endswith(':'):
                        try:
                            current_movie_id = int(line[:-1])
                            results['movie_ids_found'].add(current_movie_id)
                        except ValueError:
                            results['issues'].append(f'Invalid movie ID line: {line}')
                    else:
                        try:
                            parts = line.split(',')
                            if len(parts) == 3:
                                user_id = int(parts[0])
                                rating = int(parts[1])
                                date = parts[2].strip()
                                
                                # Validate rating range
                                if rating not in [1, 2, 3, 4, 5]:
                                    results['issues'].append(
                                        f'Invalid rating: {rating}'
                                    )
                                else:
                                    ratings.append(rating)
                                    valid_count += 1
                            else:
                                results['issues'].append(
                                    f'Invalid format: {line}'
                                )
                        except ValueError as e:
                            results['issues'].append(f'Parse error: {e}')
        
        if ratings:
            results['rating_range'] = (min(ratings), max(ratings))
        
        results['total_sampled'] = total_count
        results['valid_ratings'] = valid_count
        results['valid'] = valid_count > 0 and len(results['issues']) == 0
        results['movie_ids_found'] = len(results['movie_ids_found'])
        
        logger.info(f"  Sampled lines: {total_count}")
        logger.info(f"  Valid ratings: {valid_count}")
        logger.info(f"  Movie IDs found: {results['movie_ids_found']}")
        logger.info(f"  Rating range: {results['rating_range']}")
        
        self.validation_report['ratings_sample'] = results
        return results
    
    def check_data_consistency(self) -> Dict[str, bool]:
        """Check data consistency across files."""
        logger.info("Checking data consistency...")
        
        results = {}
        
        # Check that movie IDs in ratings exist in movie_titles
        movie_file = self.data_dir / 'movie_titles.csv'
        
        if movie_file.exists():
            try:
                titles_df = pd.read_csv(
                    movie_file,
                    header=None,
                    names=['movie_id', 'year', 'title'],
                    encoding='latin-1'
                )
                valid_movie_ids = set(titles_df['movie_id'])
                results['movie_ids_in_titles'] = len(valid_movie_ids)
                logger.info(f"  Valid movie IDs in titles: {len(valid_movie_ids)}")
            except Exception as e:
                logger.error(f"  Error reading titles: {e}")
        
        self.validation_report['consistency'] = results
        return results
    
    def generate_report(self) -> str:
        """Generate a validation report."""
        logger.info("\n" + "="*70)
        logger.info("NETFLIX DATASET VALIDATION REPORT")
        logger.info("="*70)
        
        # Files check
        files_check = self.validation_report.get('files_exist', {})
        files_ok = all(files_check.values())
        logger.info(f"\n[{'✓' if files_ok else '✗'}] Files Check")
        for filename, exists in files_check.items():
            logger.info(f"  {'✓' if exists else '✗'} {filename}")
        
        # Movie titles check
        titles_check = self.validation_report.get('movie_titles', {})
        logger.info(f"\n[{'✓' if titles_check.get('valid') else '✗'}] Movie Titles Format")
        logger.info(f"  Total movies: {titles_check.get('total_movies', 'N/A')}")
        if titles_check.get('issues'):
            for issue in titles_check['issues']:
                logger.info(f"  ⚠ {issue}")
        
        # Ratings format check
        ratings_check = self.validation_report.get('ratings_sample', {})
        logger.info(f"\n[{'✓' if ratings_check.get('valid') else '✗'}] Ratings Format (Sample)")
        logger.info(f"  Lines sampled: {ratings_check.get('total_sampled', 'N/A')}")
        logger.info(f"  Valid ratings: {ratings_check.get('valid_ratings', 'N/A')}")
        logger.info(f"  Unique movies in sample: {ratings_check.get('movie_ids_found', 'N/A')}")
        logger.info(f"  Rating range: {ratings_check.get('rating_range', 'N/A')}")
        if ratings_check.get('issues'):
            for issue in ratings_check['issues'][:5]:  # Show first 5
                logger.info(f"  ⚠ {issue}")
        
        # Consistency check
        consistency = self.validation_report.get('consistency', {})
        logger.info(f"\n[✓] Data Consistency")
        logger.info(f"  Valid movie IDs available: {consistency.get('movie_ids_in_titles', 'N/A')}")
        
        # Summary
        all_valid = (
            files_ok and 
            titles_check.get('valid', False) and 
            ratings_check.get('valid', False)
        )
        
        logger.info("\n" + "="*70)
        logger.info(f"OVERALL STATUS: {'✓ VALID' if all_valid else '✗ ISSUES FOUND'}")
        logger.info("="*70)
        
        return "validation_complete"
    
    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        self.check_files_exist()
        self.check_movie_titles_format()
        self.sample_ratings_format()
        self.check_data_consistency()
        self.generate_report()
        
        return all([
            self.validation_report.get('files_exist', {}).get('movie_titles.csv', False),
            self.validation_report.get('movie_titles', {}).get('valid', False),
            self.validation_report.get('ratings_sample', {}).get('valid', False)
        ])


def main():
    """Run validation."""
    validator = NetflixDataValidator()
    success = validator.run_all_checks()
    return success


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
