"""
Core utilities for reading SAS datasets and handling SAS data formats.
"""
import os
import pandas as pd
import numpy as np
import pyreadstat
from typing import Dict, List, Optional, Tuple, Union, Any


def read_sas(file_path: str) -> Tuple[pd.DataFrame, dict]:
    """
    Read a SAS dataset (.sas7bdat) file into a pandas DataFrame.
    
    Args:
        file_path: Path to SAS dataset file
        
    Returns:
        Tuple of (DataFrame, metadata)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"SAS dataset file not found: {file_path}")
    
    if file_path.lower().endswith('.sas7bdat'):
        df, meta = pyreadstat.read_sas7bdat(file_path)
    elif file_path.lower().endswith('.xpt'):
        df, meta = pyreadstat.read_xport(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}. Must be .sas7bdat or .xpt")
    
    return df, meta


def apply_formats_and_labels(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """
    Apply SAS formats and labels to pandas DataFrame.
    
    Args:
        df: DataFrame read from SAS dataset
        meta: Metadata from pyreadstat
        
    Returns:
        DataFrame with formats and labels applied
    """
    if 'column_names_to_labels' in meta and meta['column_names_to_labels']:
        df.columns = [
            f"{col} ({meta['column_names_to_labels'].get(col, '')})" 
            if meta['column_names_to_labels'].get(col) 
            else col 
            for col in df.columns
        ]
    
    return df


def convert_sas_dates(df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame:
    """
    Convert SAS dates (days since January 1, 1960) to Python datetime objects.
    
    Args:
        df: DataFrame containing SAS dates
        date_columns: List of column names containing SAS dates
        
    Returns:
        DataFrame with converted dates
    """
    result = df.copy()
    for col in date_columns:
        if col in result.columns:
            result[col] = pd.to_datetime(result[col], unit='D', origin='1960-01-01')
    
    return result


def convert_sas_datetimes(df: pd.DataFrame, datetime_columns: List[str]) -> pd.DataFrame:
    """
    Convert SAS datetimes (seconds since January 1, 1960) to Python datetime objects.
    
    Args:
        df: DataFrame containing SAS datetimes
        datetime_columns: List of column names containing SAS datetimes
        
    Returns:
        DataFrame with converted datetimes
    """
    result = df.copy()
    for col in datetime_columns:
        if col in result.columns:
            result[col] = pd.to_datetime(result[col], unit='s', origin='1960-01-01')
    
    return result


def convert_sas_times(df: pd.DataFrame, time_columns: List[str]) -> pd.DataFrame:
    """
    Convert SAS times (seconds since midnight) to Python timedelta objects.
    
    Args:
        df: DataFrame containing SAS times
        time_columns: List of column names containing SAS times
        
    Returns:
        DataFrame with converted times
    """
    result = df.copy()
    for col in time_columns:
        if col in result.columns:
            result[col] = pd.to_timedelta(result[col], unit='s')
    
    return result


def handle_sas_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle SAS missing values, including special missing values (.A to .Z).
    
    Args:
        df: DataFrame potentially containing SAS missing values
        
    Returns:
        DataFrame with missing values handled
    """
    missing_map = {v: None for v in ["."] + [f".{c}" for c in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")]}
    
    result = df.copy()
    result.replace(missing_map, inplace=True)
    
    return result


def sas_sort_order(df: pd.DataFrame, by_vars: List[str]) -> pd.DataFrame:
    """
    Sort DataFrame to match SAS sort behavior (missing values first).
    
    Args:
        df: DataFrame to sort
        by_vars: Variables to sort by
        
    Returns:
        Sorted DataFrame
    """
    result = df.sort_values(by_vars, na_position='first')
    return result
