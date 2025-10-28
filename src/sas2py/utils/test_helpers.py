"""
Test helpers for parity testing between SAS and Python outputs.
"""
import numpy as np
import pandas as pd
from typing import List, Optional, Union, Any


def assert_frame_equalish(
    a: pd.DataFrame, 
    b: pd.DataFrame, 
    *,
    abs_tol: float = 1.0e-9, 
    rel_tol: float = 1.0e-6, 
    sort_by: Optional[List[str]] = None
):
    """
    Assert that two DataFrames are equal within specified tolerances.
    
    Args:
        a: First DataFrame
        b: Second DataFrame
        abs_tol: Absolute tolerance for numeric comparisons
        rel_tol: Relative tolerance for numeric comparisons
        sort_by: Columns to sort by before comparison
        
    Raises:
        AssertionError: If DataFrames are not equivalent within tolerances
    """
    if sort_by:
        a = a.sort_values(sort_by).reset_index(drop=True)
        b = b.sort_values(sort_by).reset_index(drop=True)
    
    assert len(a) == len(b), f"Row counts differ: {len(a)} vs {len(b)}"
    
    assert set(a.columns) == set(b.columns), f"Column sets differ: {set(a.columns) - set(b.columns)} | {set(b.columns) - set(a.columns)}"
    
    b = b[a.columns]
    
    for c in a.columns:
        if np.issubdtype(a[c].dtype, np.number) and np.issubdtype(b[c].dtype, np.number):
            np.testing.assert_allclose(
                a[c].to_numpy(), 
                b[c].to_numpy(),
                rtol=rel_tol, 
                atol=abs_tol, 
                equal_nan=True,
                err_msg=f"Numeric values differ in column {c}"
            )
        else:
            pd.testing.assert_series_equal(
                a[c].astype("string").fillna("<NA>"),
                b[c].astype("string").fillna("<NA>"),
                check_names=False,
                check_index=False,
                check_dtype=False,
                obj=f"String values differ in column {c}"
            )


def create_comparison_report(
    a: pd.DataFrame, 
    b: pd.DataFrame,
    name_a: str = "SAS",
    name_b: str = "Python",
    numeric_cols: Optional[List[str]] = None,
    key_cols: Optional[List[str]] = None,
    abs_tol: float = 1.0e-9,
    rel_tol: float = 1.0e-6
) -> dict:
    """
    Create a detailed comparison report between two DataFrames.
    
    Args:
        a: First DataFrame (typically SAS output)
        b: Second DataFrame (typically Python output)
        name_a: Name for the first DataFrame (e.g., "SAS")
        name_b: Name for the second DataFrame (e.g., "Python")
        numeric_cols: List of numeric columns to compare
        key_cols: List of key columns (identifiers, not values)
        abs_tol: Absolute tolerance for numeric comparisons
        rel_tol: Relative tolerance for numeric comparisons
        
    Returns:
        Dictionary with comparison results
    """
    report = {
        "row_counts": {
            name_a: len(a),
            name_b: len(b),
            "match": len(a) == len(b),
            "diff": abs(len(a) - len(b))
        },
        "column_counts": {
            name_a: len(a.columns),
            name_b: len(b.columns),
            "match": len(a.columns) == len(b.columns),
            "diff": abs(len(a.columns) - len(b.columns))
        },
        "columns_only_in_a": list(set(a.columns) - set(b.columns)),
        "columns_only_in_b": list(set(b.columns) - set(a.columns)),
        "common_columns": list(set(a.columns) & set(b.columns)),
        "numeric_comparison": {},
        "key_comparison": {},
        "overall_match": False
    }
    
    common_cols = report["common_columns"]
    
    if numeric_cols is None:
        numeric_cols = [
            c for c in common_cols 
            if np.issubdtype(a[c].dtype, np.number) and np.issubdtype(b[c].dtype, np.number)
        ]
    else:
        numeric_cols = [c for c in numeric_cols if c in common_cols]
    
    for col in numeric_cols:
        a_values = a[col].dropna()
        b_values = b[col].dropna()
        
        a_stats = {
            "mean": a_values.mean() if len(a_values) > 0 else None,
            "std": a_values.std() if len(a_values) > 0 else None,
            "min": a_values.min() if len(a_values) > 0 else None,
            "max": a_values.max() if len(a_values) > 0 else None,
            "count": len(a_values),
            "null_count": a[col].isna().sum()
        }
        
        b_stats = {
            "mean": b_values.mean() if len(b_values) > 0 else None,
            "std": b_values.std() if len(b_values) > 0 else None,
            "min": b_values.min() if len(b_values) > 0 else None,
            "max": b_values.max() if len(b_values) > 0 else None,
            "count": len(b_values),
            "null_count": b[col].isna().sum()
        }
        
        mean_diff = abs(a_stats["mean"] - b_stats["mean"]) if (a_stats["mean"] is not None and b_stats["mean"] is not None) else None
        mean_rel_diff = (mean_diff / abs(a_stats["mean"])) if (mean_diff is not None and a_stats["mean"] != 0) else None
        
        within_tol = False
        if mean_diff is not None:
            within_tol = (mean_diff <= abs_tol) or (mean_rel_diff is not None and mean_rel_diff <= rel_tol)
        
        report["numeric_comparison"][col] = {
            name_a: a_stats,
            name_b: b_stats,
            "mean_abs_diff": mean_diff,
            "mean_rel_diff": mean_rel_diff,
            "within_tolerance": within_tol
        }
    
    if key_cols:
        key_cols = [c for c in key_cols if c in common_cols]
        
        for col in key_cols:
            a_unique = a[col].nunique()
            b_unique = b[col].nunique()
            a_values = set(a[col].dropna().unique())
            b_values = set(b[col].dropna().unique())
            
            report["key_comparison"][col] = {
                f"{name_a}_unique": a_unique,
                f"{name_b}_unique": b_unique,
                "match": a_unique == b_unique,
                "only_in_a": list(a_values - b_values)[:10],  # Limit to first 10
                "only_in_b": list(b_values - a_values)[:10],  # Limit to first 10
                "common_count": len(a_values & b_values)
            }
    
    row_match = report["row_counts"]["match"]
    col_match = len(report["columns_only_in_a"]) == 0 and len(report["columns_only_in_b"]) == 0
    numeric_match = all(v["within_tolerance"] for v in report["numeric_comparison"].values())
    
    report["overall_match"] = row_match and col_match and numeric_match
    
    return report


def compare_datasets(
    sas_df: pd.DataFrame, 
    py_df: pd.DataFrame,
    key_cols: Optional[List[str]] = None,
    abs_tol: float = 1.0e-9,
    rel_tol: float = 1.0e-6,
    verbose: bool = True
) -> bool:
    """
    Compare SAS and Python datasets and print a summary of differences.
    
    Args:
        sas_df: SAS output DataFrame
        py_df: Python output DataFrame
        key_cols: List of key columns (identifiers, not values)
        abs_tol: Absolute tolerance for numeric comparisons
        rel_tol: Relative tolerance for numeric comparisons
        verbose: Whether to print comparison results
        
    Returns:
        Boolean indicating whether datasets match within tolerance
    """
    report = create_comparison_report(
        sas_df, py_df, 
        name_a="SAS", 
        name_b="Python",
        key_cols=key_cols,
        abs_tol=abs_tol,
        rel_tol=rel_tol
    )
    
    if verbose:
        print(f"Row counts: SAS={report['row_counts']['SAS']}, Python={report['row_counts']['Python']} - Match: {report['row_counts']['match']}")
        print(f"Column counts: SAS={report['column_counts']['SAS']}, Python={report['column_counts']['Python']} - Match: {report['column_counts']['match']}")
        
        if report['columns_only_in_a']:
            print(f"Columns only in SAS: {report['columns_only_in_a']}")
        
        if report['columns_only_in_b']:
            print(f"Columns only in Python: {report['columns_only_in_b']}")
        
        print("\nNumeric column comparison:")
        for col, data in report['numeric_comparison'].items():
            print(f"  {col}: {'✓' if data['within_tolerance'] else '✗'} (diff: {data['mean_abs_diff']})")
        
        if report['key_comparison']:
            print("\nKey column comparison:")
            for col, data in report['key_comparison'].items():
                print(f"  {col}: {'✓' if data['match'] else '✗'} (SAS unique: {data['SAS_unique']}, Python unique: {data['Python_unique']})")
        
        print(f"\nOverall match: {'✓' if report['overall_match'] else '✗'}")
    
    return report['overall_match']
