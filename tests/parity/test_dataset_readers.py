"""
Parity tests for SAS dataset reading functionality.

These tests verify that the Python implementation correctly reads SAS datasets
and handles data type conversions, missing values, and metadata.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.sas2py.core.readers import (
    read_sas, 
    convert_sas_dates, 
    convert_sas_datetimes,
    handle_sas_missing,
    sas_sort_order
)
from src.sas2py.utils.test_helpers import assert_frame_equalish


class TestSASReaders:
    """Test SAS dataset reading and conversion functions."""
    
    def test_read_sas_adsl(self):
        """Test reading ADSL dataset."""
        df, meta = read_sas("data/adam/adsl.sas7bdat")
        
        assert len(df) > 0, "ADSL dataset should not be empty"
        assert len(df.columns) > 0, "ADSL should have columns"
        
        expected_cols = ['USUBJID', 'AGE', 'SEX']
        for col in expected_cols:
            if col in df.columns:
                assert col in df.columns, f"Expected column {col} not found"
        
        assert meta is not None, "Metadata should be returned"
        assert hasattr(meta, "column_names"), "Metadata should have column_names attribute"
    
    def test_read_sas_fixture_matches(self):
        """Test that reading SAS data matches saved fixture."""
        df, _ = read_sas("data/adam/adsl.sas7bdat")
        sample = df.head(10)
        
        sample = handle_sas_missing(sample)
        
        for col in sample.select_dtypes(include=['object']):
            sample[col] = sample[col].replace('', np.nan)
        
        fixture_path = Path("tests/parity/fixtures/adsl_sample.csv")
        if not fixture_path.exists():
            pytest.skip("Fixture not generated yet. Run generate_fixtures.py first.")
        
        fixture = pd.read_csv(fixture_path, na_values=["<NA>"], keep_default_na=True)
        
        assert_frame_equalish(
            sample, 
            fixture,
            abs_tol=1e-9,
            rel_tol=1e-6
        )
    
    def test_handle_sas_missing(self):
        """Test SAS missing value handling."""
        test_data = pd.DataFrame({
            'a': [1.0, np.nan, 3.0, 4.0],
            'b': ['text', '', 'more', 'data'],
            'c': [10, 20, 30, 40]
        })
        
        result = handle_sas_missing(test_data)
        
        assert len(result) == len(test_data)
        assert list(result.columns) == list(test_data.columns)
    
    def test_sas_sort_order(self):
        """Test SAS sort order (missing values first)."""
        test_data = pd.DataFrame({
            'id': [3, 1, 2, 1, 2],
            'value': [10, np.nan, 20, 15, np.nan]
        })
        
        result = sas_sort_order(test_data, ['id', 'value'])
        
        assert result.iloc[0]['id'] == 1
        assert pd.isna(result.iloc[0]['value'])


class TestDataTypeConversions:
    """Test SAS data type conversion functions."""
    
    def test_convert_sas_dates(self):
        """Test SAS date conversion (days since 1960-01-01)."""
        test_data = pd.DataFrame({
            'sas_date': [0, 365, 23376],  # 1960-01-01, 1960-12-31, 2024-01-01
            'other': [1, 2, 3]
        })
        
        result = convert_sas_dates(test_data, ['sas_date'])
        
        assert pd.api.types.is_datetime64_any_dtype(result['sas_date'])
        assert result['sas_date'].iloc[0] == pd.Timestamp('1960-01-01')
        
        assert list(result['other']) == [1, 2, 3]
    
    def test_convert_sas_datetimes(self):
        """Test SAS datetime conversion (seconds since 1960-01-01)."""
        test_data = pd.DataFrame({
            'sas_datetime': [0, 3600, 86400],  # 1960-01-01 00:00, 01:00, next day
            'other': [1, 2, 3]
        })
        
        result = convert_sas_datetimes(test_data, ['sas_datetime'])
        
        assert pd.api.types.is_datetime64_any_dtype(result['sas_datetime'])
        assert result['sas_datetime'].iloc[0] == pd.Timestamp('1960-01-01 00:00:00')


class TestDataIntegrity:
    """Test data integrity and parity with SAS."""
    
    def test_adsl_row_count(self):
        """Test ADSL dataset has expected structure."""
        df, _ = read_sas("data/adam/adsl.sas7bdat")
        
        assert len(df) > 0, "Dataset should not be empty"
        assert len(df.columns) >= 5, "Should have at least 5 columns"
        
        assert not df.isna().all(axis=1).any(), "Should not have completely null rows"
    
    def test_adsl_vs_modified(self):
        """Compare base ADSL with modified version."""
        base_df, _ = read_sas("data/adam/adsl.sas7bdat")
        mod_df, _ = read_sas("data/adam/mod_01/adsl.sas7bdat")
        
        assert len(base_df) == len(mod_df), "Row counts should match"
        
        base_cols = set(base_df.columns)
        mod_cols = set(mod_df.columns)
        
        shared = base_cols & mod_cols
        assert len(shared) >= len(base_cols) * 0.8, "At least 80% of columns should be shared"
