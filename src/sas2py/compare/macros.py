"""
Python implementation of SAS comparison macros (compvars, complibs, compare).
Translates the functionality from test_compare_macros.sas.
"""
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from ..core.readers import read_sas, handle_sas_missing

logger = logging.getLogger(__name__)


def compvars(ds1: pd.DataFrame, ds2: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """
    Compare variable lists between two datasets.
    Python implementation of %compvars SAS macro.
    
    Args:
        ds1: First dataset
        ds2: Second dataset
        
    Returns:
        Tuple of (variables in ds1 only, variables in ds2 only, variables in both)
    """
    vars1 = set(ds1.columns)
    vars2 = set(ds2.columns)
    
    vars_left = list(vars1 - vars2)  # In ds1 only
    vars_right = list(vars2 - vars1)  # In ds2 only
    vars_both = list(vars1 & vars2)   # In both
    
    logger.info(f"Variables found in ds1 but not ds2: {', '.join(vars_left) if vars_left else 'None'}")
    logger.info(f"Variables found in ds2 but not ds1: {', '.join(vars_right) if vars_right else 'None'}")
    logger.info(f"Variables found in both datasets: {', '.join(vars_both) if vars_both else 'None'}")
    
    return vars_left, vars_right, vars_both


def complibs(lib1_path: str, lib2_path: str, sortvars: Optional[List[str]] = None) -> Dict[str, Dict]:
    """
    Compare all matching datasets in two libraries.
    Python implementation of %complibs SAS macro.
    
    Args:
        lib1_path: Path to first library (directory with SAS datasets)
        lib2_path: Path to second library (directory with SAS datasets)
        sortvars: Variables to sort by before comparison
        
    Returns:
        Dictionary with comparison results for each matching dataset
    """
    if not os.path.isdir(lib1_path):
        raise ValueError(f"First library path is not a directory: {lib1_path}")
    if not os.path.isdir(lib2_path):
        raise ValueError(f"Second library path is not a directory: {lib2_path}")
    
    lib1_files = [f for f in os.listdir(lib1_path) if f.lower().endswith('.sas7bdat')]
    lib2_files = [f for f in os.listdir(lib2_path) if f.lower().endswith('.sas7bdat')]
    
    lib1_names = [os.path.splitext(f)[0].lower() for f in lib1_files]
    lib2_names = [os.path.splitext(f)[0].lower() for f in lib2_files]
    
    common_datasets = set(lib1_names) & set(lib2_names)
    
    results = {}
    
    for dataset in common_datasets:
        logger.info(f"Comparing dataset: {dataset}")
        
        lib1_file = next(f for f in lib1_files if os.path.splitext(f)[0].lower() == dataset)
        lib2_file = next(f for f in lib2_files if os.path.splitext(f)[0].lower() == dataset)
        
        ds1, meta1 = read_sas(os.path.join(lib1_path, lib1_file))
        ds2, meta2 = read_sas(os.path.join(lib2_path, lib2_file))
        
        ds1 = handle_sas_missing(ds1)
        ds2 = handle_sas_missing(ds2)
        
        if sortvars:
            sort_vars = [v for v in sortvars if v in ds1.columns and v in ds2.columns]
            if sort_vars:
                ds1 = ds1.sort_values(sort_vars).reset_index(drop=True)
                ds2 = ds2.sort_values(sort_vars).reset_index(drop=True)
        
        vars_left, vars_right, vars_both = compvars(ds1, ds2)
        
        row_count_match = len(ds1) == len(ds2)
        
        comp_result = compare(
            ds1[vars_both] if vars_both else pd.DataFrame(),
            ds2[vars_both] if vars_both else pd.DataFrame(),
            by=sortvars
        )
        
        results[dataset] = {
            'row_count_match': row_count_match,
            'ds1_rows': len(ds1),
            'ds2_rows': len(ds2),
            'vars_left': vars_left,
            'vars_right': vars_right,
            'vars_both': vars_both,
            'comparison': comp_result
        }
    
    return results


def compare(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    by: Optional[List[str]] = None,
    numeric_abs_tol: float = 1.0e-9,
    numeric_rel_tol: float = 1.0e-6
) -> Dict[str, Any]:
    """
    Compare two datasets in detail.
    Python implementation of %compare SAS macro and PROC COMPARE.
    
    Args:
        base: Base dataset for comparison
        comp: Comparison dataset
        by: Variables to match observations by
        numeric_abs_tol: Absolute tolerance for numeric comparisons
        numeric_rel_tol: Relative tolerance for numeric comparisons
        
    Returns:
        Dictionary with comparison results
    """
    result = {
        'row_count_match': len(base) == len(comp),
        'base_rows': len(base),
        'comp_rows': len(comp),
        'column_count_match': len(base.columns) == len(comp.columns),
        'base_columns': len(base.columns),
        'comp_columns': len(comp.columns),
        'column_names_match': set(base.columns) == set(comp.columns),
        'differences': []
    }
    
    if by and all(b in base.columns for b in by) and all(b in comp.columns for b in by):
        base_sorted = base.sort_values(by).reset_index(drop=True)
        comp_sorted = comp.sort_values(by).reset_index(drop=True)
        
        base_groups = base_sorted.groupby(by)
        comp_groups = comp_sorted.groupby(by)
        
        base_keys = set(map(tuple, base_sorted[by].values))
        comp_keys = set(map(tuple, comp_sorted[by].values))
        
        base_only_keys = base_keys - comp_keys
        comp_only_keys = comp_keys - base_keys
        common_keys = base_keys & comp_keys
        
        result['by_group_count_match'] = len(base_keys) == len(comp_keys)
        result['base_only_groups'] = len(base_only_keys)
        result['comp_only_groups'] = len(comp_only_keys)
        result['common_groups'] = len(common_keys)
        
        differences = []
        for key in common_keys:
            if isinstance(key, tuple):
                key_dict = {by[i]: key[i] for i in range(len(by))}
                base_group = base_sorted.loc[(base_sorted[list(key_dict.keys())] == pd.Series(key_dict)).all(axis=1)]
                comp_group = comp_sorted.loc[(comp_sorted[list(key_dict.keys())] == pd.Series(key_dict)).all(axis=1)]
            else:
                base_group = base_sorted.loc[base_sorted[by[0]] == key]
                comp_group = comp_sorted.loc[comp_sorted[by[0]] == key]
            
            for col in set(base_group.columns) & set(comp_group.columns):
                if col not in by:
                    base_vals = base_group[col].values
                    comp_vals = comp_group[col].values
                    
                    if len(base_vals) != len(comp_vals):
                        differences.append({
                            'by_values': key,
                            'variable': col,
                            'issue': 'row_count_mismatch',
                            'base_rows': len(base_vals),
                            'comp_rows': len(comp_vals)
                        })
                        continue
                    
                    if base_group[col].dtype.kind in 'fc' and comp_group[col].dtype.kind in 'fc':
                        for i, (base_val, comp_val) in enumerate(zip(base_vals, comp_vals)):
                            if pd.isna(base_val) and pd.isna(comp_val):
                                continue
                            elif pd.isna(base_val) or pd.isna(comp_val):
                                differences.append({
                                    'by_values': key,
                                    'variable': col,
                                    'row': i,
                                    'base_value': base_val,
                                    'comp_value': comp_val,
                                    'issue': 'missing_value_mismatch'
                                })
                            elif not np.isclose(base_val, comp_val, 
                                              rtol=numeric_rel_tol, 
                                              atol=numeric_abs_tol):
                                differences.append({
                                    'by_values': key,
                                    'variable': col,
                                    'row': i,
                                    'base_value': base_val,
                                    'comp_value': comp_val,
                                    'issue': 'value_mismatch',
                                    'difference': comp_val - base_val
                                })
                    else:
                        for i, (base_val, comp_val) in enumerate(zip(base_vals, comp_vals)):
                            if pd.isna(base_val) and pd.isna(comp_val):
                                continue
                            elif pd.isna(base_val) or pd.isna(comp_val):
                                differences.append({
                                    'by_values': key,
                                    'variable': col,
                                    'row': i,
                                    'base_value': base_val,
                                    'comp_value': comp_val,
                                    'issue': 'missing_value_mismatch'
                                })
                            elif base_val != comp_val:
                                differences.append({
                                    'by_values': key,
                                    'variable': col,
                                    'row': i,
                                    'base_value': base_val,
                                    'comp_value': comp_val,
                                    'issue': 'value_mismatch'
                                })
    else:
        if len(base) != len(comp):
            result['differences'].append({
                'issue': 'row_count_mismatch',
                'base_rows': len(base),
                'comp_rows': len(comp)
            })
        
        common_vars = list(set(base.columns) & set(comp.columns))
        
        min_rows = min(len(base), len(comp))
        
        for col in common_vars:
            base_col = base[col].iloc[:min_rows]
            comp_col = comp[col].iloc[:min_rows]
            
            if base_col.dtype.kind in 'fc' and comp_col.dtype.kind in 'fc':
                for i, (base_val, comp_val) in enumerate(zip(base_col, comp_col)):
                    if pd.isna(base_val) and pd.isna(comp_val):
                        continue
                    elif pd.isna(base_val) or pd.isna(comp_val):
                        result['differences'].append({
                            'variable': col,
                            'row': i,
                            'base_value': base_val,
                            'comp_value': comp_val,
                            'issue': 'missing_value_mismatch'
                        })
                    elif not np.isclose(base_val, comp_val, 
                                      rtol=numeric_rel_tol, 
                                      atol=numeric_abs_tol):
                        result['differences'].append({
                            'variable': col,
                            'row': i,
                            'base_value': base_val,
                            'comp_value': comp_val,
                            'issue': 'value_mismatch',
                            'difference': comp_val - base_val
                        })
            else:
                for i, (base_val, comp_val) in enumerate(zip(base_col, comp_col)):
                    if pd.isna(base_val) and pd.isna(comp_val):
                        continue
                    elif pd.isna(base_val) or pd.isna(comp_val):
                        result['differences'].append({
                            'variable': col,
                            'row': i,
                            'base_value': base_val,
                            'comp_value': comp_val,
                            'issue': 'missing_value_mismatch'
                        })
                    elif base_val != comp_val:
                        result['differences'].append({
                            'variable': col,
                            'row': i,
                            'base_value': base_val,
                            'comp_value': comp_val,
                            'issue': 'value_mismatch'
                        })
    
    result['match'] = len(result['differences']) == 0
    result['difference_count'] = len(result['differences'])
    
    return result
