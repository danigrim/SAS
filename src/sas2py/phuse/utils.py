"""
Python implementation of PhUSE utility macros for clinical data visualization.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any


def get_parameter_metadata(df: pd.DataFrame, 
                          param_code_col: str, 
                          param_label_col: str) -> Dict[str, str]:
    """
    Extract parameter codes and labels.
    Python implementation of %util_labels_from_var PhUSE macro.
    
    Args:
        df: DataFrame containing parameter data
        param_code_col: Column name for parameter code
        param_label_col: Column name for parameter label
        
    Returns:
        Dictionary mapping parameter codes to labels
    """
    param_data = df[[param_code_col, param_label_col]].drop_duplicates().dropna()
    
    param_dict = dict(zip(param_data[param_code_col], param_data[param_label_col]))
    
    return param_dict


def count_unique_values(df: pd.DataFrame, column: str) -> int:
    """
    Count distinct values of a variable.
    Python implementation of %util_count_unique_values PhUSE macro.
    
    Args:
        df: DataFrame containing data
        column: Column name to count unique values
        
    Returns:
        Count of unique values
    """
    return df[column].nunique()


def get_reference_lines(
    df: pd.DataFrame, 
    var_col: str, 
    ref_type: str = 'UNIFORM',
    low_col: Optional[str] = None,
    high_col: Optional[str] = None,
    fixed_values: Optional[List[float]] = None
) -> List[float]:
    """
    Calculate reference lines for plots.
    Python implementation of %util_get_reference_lines PhUSE macro.
    
    Args:
        df: DataFrame containing data
        var_col: Column name for the measured variable
        ref_type: Type of reference lines ('NONE', 'UNIFORM', 'NARROW', 'ALL', or numeric values)
        low_col: Column name for lower reference limit
        high_col: Column name for upper reference limit
        fixed_values: List of fixed reference line values
        
    Returns:
        List of reference line values
    """
    if ref_type == 'NONE' or (not low_col and not high_col and not fixed_values):
        return []
    
    ref_lines = []
    
    if fixed_values:
        ref_lines.extend(fixed_values)
    
    if ref_type in ['UNIFORM', 'ALL']:
        data_min = df[var_col].min()
        data_max = df[var_col].max()
        
        if low_col and high_col:
            low_vals = df[low_col].dropna().unique()
            high_vals = df[high_col].dropna().unique()
            
            ref_lines.extend(low_vals)
            ref_lines.extend(high_vals)
    
    elif ref_type == 'NARROW':
        if low_col and high_col:
            ranges = df[[low_col, high_col]].dropna().drop_duplicates()
            
            if len(ranges) > 0:
                most_common_range = ranges.iloc[0]
                ref_lines.append(most_common_range[0])  # low
                ref_lines.append(most_common_range[1])  # high
    
    ref_lines = sorted(list(set([x for x in ref_lines if not pd.isna(x)])))
    
    return ref_lines


def get_var_min_max(df: pd.DataFrame, var_col: str, padding: float = 0.1) -> Tuple[float, float]:
    """
    Determine axis ranges for plots.
    Python implementation of %util_get_var_min_max PhUSE macro.
    
    Args:
        df: DataFrame containing data
        var_col: Column name for the measured variable
        padding: Fraction of range to add as padding (default: 0.1 or 10%)
        
    Returns:
        Tuple of (min, max) values for axis range
    """
    data = df[var_col].dropna()
    
    if len(data) == 0:
        return (0, 1)  # Default range if no data
    
    data_min = data.min()
    data_max = data.max()
    data_range = data_max - data_min
    
    padded_min = data_min - (data_range * padding)
    padded_max = data_max + (data_range * padding)
    
    return (padded_min, padded_max)


def value_format(value: float, precision: int = 2) -> str:
    """
    Format statistical values with appropriate precision.
    Python implementation of %util_value_format PhUSE macro.
    
    Args:
        value: Numeric value to format
        precision: Number of decimal places
        
    Returns:
        Formatted string representation
    """
    if pd.isna(value):
        return ''
    
    return f'{value:.{precision}f}'


def boxplot_block_ranges(
    df: pd.DataFrame, 
    visit_col: str, 
    max_boxes_per_page: int = 20
) -> List[Tuple[int, int]]:
    """
    Paginate visits into plot pages.
    Python implementation of %util_boxplot_block_ranges PhUSE macro.
    
    Args:
        df: DataFrame containing data
        visit_col: Column name for visit/timepoint
        max_boxes_per_page: Maximum number of boxes per page
        
    Returns:
        List of (start_idx, end_idx) tuples for each page
    """
    visits = sorted(df[visit_col].unique())
    
    n_visits = len(visits)
    n_pages = (n_visits + max_boxes_per_page - 1) // max_boxes_per_page
    
    page_ranges = []
    for i in range(n_pages):
        start_idx = i * max_boxes_per_page
        end_idx = min((i + 1) * max_boxes_per_page - 1, n_visits - 1)
        page_ranges.append((start_idx, end_idx))
    
    return page_ranges


def axis_order(
    min_val: float, 
    max_val: float,
    n_ticks: int = 5
) -> Tuple[float, float, float]:
    """
    Calculate axis tick intervals.
    Python implementation of %util_axis_order PhUSE macro.
    
    Args:
        min_val: Minimum axis value
        max_val: Maximum axis value
        n_ticks: Desired number of tick marks
        
    Returns:
        Tuple of (min, max, tick_interval)
    """
    range_val = max_val - min_val
    
    raw_interval = range_val / (n_ticks - 1)
    
    magnitude = 10 ** np.floor(np.log10(raw_interval))
    mantissa = raw_interval / magnitude
    
    if mantissa < 1.5:
        tick_interval = magnitude
    elif mantissa < 3:
        tick_interval = 2 * magnitude
    elif mantissa < 7:
        tick_interval = 5 * magnitude
    else:
        tick_interval = 10 * magnitude
    
    adj_min = np.floor(min_val / tick_interval) * tick_interval
    adj_max = np.ceil(max_val / tick_interval) * tick_interval
    
    return (adj_min, adj_max, tick_interval)
