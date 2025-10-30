"""
Parity tests for dataset comparison functionality.

These tests verify that the Python implementations of SAS comparison macros
(compvars, complibs, compare) produce correct and consistent results.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.sas2py.core.readers import read_sas
from src.sas2py.compare.macros import compvars, complibs, compare


class TestCompvars:
    """Test the compvars macro (variable comparison)."""
    
    def test_compvars_identical_datasets(self):
        """Test compvars with identical datasets."""
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
        df2 = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
        
        vars_left, vars_right, vars_both = compvars(df1, df2)
        
        assert len(vars_left) == 0, "Should have no variables only in left"
        assert len(vars_right) == 0, "Should have no variables only in right"
        assert len(vars_both) == 3, "Should have 3 variables in both"
        assert set(vars_both) == {'a', 'b', 'c'}
    
    def test_compvars_different_columns(self):
        """Test compvars with different column sets."""
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
        df2 = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'd': [7, 8]})
        
        vars_left, vars_right, vars_both = compvars(df1, df2)
        
        assert vars_left == ['c'], "Column 'c' only in left"
        assert vars_right == ['d'], "Column 'd' only in right"
        assert set(vars_both) == {'a', 'b'}, "Columns 'a' and 'b' in both"
    
    def test_compvars_with_adsl(self):
        """Test compvars with actual ADSL datasets."""
        base_df, _ = read_sas("data/adam/adsl.sas7bdat")
        mod_df, _ = read_sas("data/adam/mod_01/adsl.sas7bdat")
        
        vars_left, vars_right, vars_both = compvars(base_df, mod_df)
        
        assert isinstance(vars_left, list)
        assert isinstance(vars_right, list)
        assert isinstance(vars_both, list)
        
        total_cols = len(set(base_df.columns) | set(mod_df.columns))
        assert len(vars_left) + len(vars_right) + len(vars_both) == total_cols


class TestCompare:
    """Test the compare macro (detailed dataset comparison)."""
    
    def test_compare_identical_datasets(self):
        """Test compare with identical datasets."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, 20.0, 30.0],
            'name': ['a', 'b', 'c']
        })
        df2 = df1.copy()
        
        result = compare(df1, df2, by=['id'])
        
        assert result['row_count_match'], "Row counts should match"
        assert result['column_names_match'], "Column names should match"
        assert result['match'], "Values should match"
    
    def test_compare_different_values(self):
        """Test compare with different values."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, 20.0, 30.0]
        })
        df2 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, 20.5, 30.0]  # Different value for id=2
        })
        
        result = compare(df1, df2)
        
        print(f"Result: {result}")
        print(f"Differences: {result['differences']}")
        
        assert not result['match'], "Values should not match"
        assert result['row_count_match'], "Row counts should match"
        assert result['column_names_match'], "Column names should match"
    
    def test_compare_within_tolerance(self):
        """Test compare with numeric values within tolerance."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, 20.0, 30.0]
        })
        df2 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, 20.0 + 1e-10, 30.0]  # Within abs_tol
        })
        
        result = compare(
            df1, df2, 
            numeric_abs_tol=1e-9,
            numeric_rel_tol=1e-6
        )
        
        assert result['match'], "Values within tolerance should match"
    
    def test_compare_missing_values(self):
        """Test compare handles missing values correctly."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, np.nan, 30.0]
        })
        df2 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.0, np.nan, 30.0]
        })
        
        result = compare(df1, df2)
        
        assert result['match'], "Matching NaN values should be considered equal"


class TestComplibs:
    """Test the complibs macro (library comparison)."""
    
    def test_complibs_adam_vs_mod(self):
        """Test complibs comparing base and modified ADAM libraries."""
        results = complibs(
            "data/adam",
            "data/adam/mod_01",
            sortvars=["USUBJID"]
        )
        
        assert isinstance(results, dict)
        assert len(results) > 0, "Should have comparison results"
        
        for dataset_name, comparison in results.items():
            assert 'vars_both' in comparison, "Should have vars_both key"
            assert 'row_count_match' in comparison, "Should have row_count_match key"


class TestParityWithFixtures:
    """Test parity using saved fixtures."""
    
    def test_comparison_with_fixtures(self):
        """Test comparison using saved fixtures."""
        fixture_path_base = Path("tests/parity/fixtures/adsl_base_sample.csv")
        fixture_path_mod = Path("tests/parity/fixtures/adsl_mod_sample.csv")
        
        if not fixture_path_base.exists() or not fixture_path_mod.exists():
            pytest.skip("Fixtures not generated yet. Run generate_fixtures.py first.")
        
        base = pd.read_csv(fixture_path_base, na_values=["<NA>"], keep_default_na=True)
        mod = pd.read_csv(fixture_path_mod, na_values=["<NA>"], keep_default_na=True)
        
        vars_left, vars_right, vars_both = compvars(base, mod)
        
        assert len(vars_both) > 0, "Should have common variables"
