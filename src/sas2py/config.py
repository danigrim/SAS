"""
Configuration module for SAS2PY package.
Handles global settings for reproducibility and output formatting.
"""
import pandas as pd
import numpy as np
import random


def set_reproducible_mode(seed: int = 42):
    """
    Set random seeds for reproducible results across numpy, random, and pandas.
    
    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    random.seed(seed)
    

def set_display_options(float_precision: int = 6, max_rows: int = 100, max_columns: int = 20):
    """
    Configure pandas display options for consistent output formatting.
    
    Args:
        float_precision: Number of decimal places for float display
        max_rows: Maximum number of rows to display
        max_columns: Maximum number of columns to display
    """
    pd.options.display.float_format = f'{{:.{float_precision}f}}'.format
    pd.options.display.max_rows = max_rows
    pd.options.display.max_columns = max_columns
    pd.options.display.width = 120
    

def initialize_sas2py(seed: int = 42, float_precision: int = 6):
    """
    Initialize SAS2PY with standard settings for reproducibility and formatting.
    
    Args:
        seed: Random seed for reproducibility
        float_precision: Number of decimal places for float display
    """
    set_reproducible_mode(seed)
    set_display_options(float_precision)


initialize_sas2py()
