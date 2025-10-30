#!/usr/bin/env python
"""
Generate golden datasets (test fixtures) from SAS data for parity testing.

This script reads SAS datasets, processes them with the Python implementation,
and saves small subsets as golden datasets for automated parity testing.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.sas2py.core.readers import read_sas, convert_sas_dates, handle_sas_missing
import pandas as pd


def create_adsl_fixture():
    """Create a small fixture from ADSL dataset."""
    print("Creating ADSL fixture...")
    
    adsl_path = "data/adam/adsl.sas7bdat"
    df, meta = read_sas(adsl_path)
    
    sample = df.head(10).copy()
    sample = handle_sas_missing(sample)
    
    output_path = "tests/parity/fixtures/adsl_sample.csv"
    sample.to_csv(output_path, index=False, na_rep="<NA>")
    
    print(f"  Saved {len(sample)} rows to {output_path}")
    print(f"  Columns: {list(sample.columns)[:5]}...")
    
    return sample


def create_comparison_fixture():
    """Create fixtures for dataset comparison testing."""
    print("Creating comparison fixtures...")
    
    base_path = "data/adam/adsl.sas7bdat"
    mod_path = "data/adam/mod_01/adsl.sas7bdat"
    
    base_df, _ = read_sas(base_path)
    mod_df, _ = read_sas(mod_path)
    
    base_sample = base_df.head(10).copy()
    mod_sample = mod_df.head(10).copy()
    
    base_sample = handle_sas_missing(base_sample)
    mod_sample = handle_sas_missing(mod_sample)
    
    base_output = "tests/parity/fixtures/adsl_base_sample.csv"
    mod_output = "tests/parity/fixtures/adsl_mod_sample.csv"
    
    base_sample.to_csv(base_output, index=False, na_rep="<NA>")
    mod_sample.to_csv(mod_output, index=False, na_rep="<NA>")
    
    print(f"  Saved base: {len(base_sample)} rows to {base_output}")
    print(f"  Saved mod: {len(mod_sample)} rows to {mod_output}")
    
    return base_sample, mod_sample


def create_adlbc_fixture():
    """Create a small fixture from ADLBC dataset for box plot testing."""
    print("Creating ADLBC fixture...")
    
    adlbc_path = "data/adam/adlbc.sas7bdat"
    df, meta = read_sas(adlbc_path)
    
    if 'PARAM' in df.columns:
        first_param = df['PARAM'].dropna().iloc[0] if len(df) > 0 else None
        if first_param:
            sample = df[df['PARAM'] == first_param].head(50).copy()
        else:
            sample = df.head(50).copy()
    else:
        sample = df.head(50).copy()
    
    sample = handle_sas_missing(sample)
    
    output_path = "tests/parity/fixtures/adlbc_sample.csv"
    sample.to_csv(output_path, index=False, na_rep="<NA>")
    
    print(f"  Saved {len(sample)} rows to {output_path}")
    print(f"  Columns: {list(sample.columns)[:5]}...")
    
    return sample


def main():
    """Generate all test fixtures."""
    print("Generating test fixtures from SAS datasets...")
    print("=" * 60)
    
    os.chdir("/home/ubuntu/repos/SAS")
    
    try:
        adsl = create_adsl_fixture()
        print(f"✓ ADSL fixture created: {len(adsl)} rows, {len(adsl.columns)} columns\n")
        
        base, mod = create_comparison_fixture()
        print(f"✓ Comparison fixtures created\n")
        
        adlbc = create_adlbc_fixture()
        print(f"✓ ADLBC fixture created: {len(adlbc)} rows, {len(adlbc.columns)} columns\n")
        
        print("=" * 60)
        print("✓ All fixtures generated successfully!")
        
    except Exception as e:
        print(f"✗ Error generating fixtures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
