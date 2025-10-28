# SAS2PY - SAS to Python Migration

This package provides tools for migrating SAS analyses, data pipelines, and statistical models to Python, focusing on clinical trial data analysis. It implements both PHUSE-compliant box plots and dataset comparison utilities based on the original SAS scripts.

## Features

- **SAS Dataset Reading**: Read SAS datasets (.sas7bdat) and transport files (.xpt) with proper metadata handling
- **Dataset Comparison**: Python implementations of SAS %compvars, %complibs, and %compare macros for validation
- **PhUSE Box Plots**: Python implementation of PhUSE box plot generation for clinical measurements
- **Date/Time Handling**: Proper conversion of SAS dates, times, and datetimes
- **Special Missing Values**: Support for SAS special missing values (.A to .Z)
- **Format/Informat Mapping**: Preservation of SAS formats and labels

## Installation

```bash
# Install using Poetry
cd /path/to/repository
poetry install

# Or install in development mode with pip
pip install -e .
```

## Usage

### Command-Line Interface

#### PhUSE Box Plots

Generate box plots for clinical measurements by visit and treatment:

```bash
# Using the CLI command
phuse-boxplot data/adam/ADLBC.sas7bdat \
  --parameters ALB,ALP,ALT \
  --visits 0,2,4,6 \
  --output-dir results/phuse_boxplots \
  --file-format html

# Or using the script directly
python scripts/phuse_boxplot.py data/adam/ADLBC.sas7bdat \
  --parameters ALB \
  --output-dir results/phuse_boxplots
```

#### Dataset Comparison

Compare variables between two datasets:

```bash
# Using the CLI command
compare-datasets compvars \
  data/adam/ADSL.sas7bdat \
  data/adam/mod_01/ADSL.sas7bdat \
  --output results/adsl_var_comparison.json

# Compare entire libraries
compare-datasets complibs \
  data/adam \
  data/adam/mod_01 \
  --sortvars USUBJID \
  --output results/library_comparison.json

# Detailed comparison with BY variables
compare-datasets compare \
  data/adam/ADAE.sas7bdat \
  data/adam/mod_01/ADAE.sas7bdat \
  --by USUBJID,ASTDY \
  --abs-tol 1e-9 \
  --rel-tol 1e-6 \
  --output results/adae_comparison.json
```

### Python API

#### Reading SAS Datasets

```python
from sas2py.core.readers import read_sas, handle_sas_missing, convert_sas_dates

# Read a SAS dataset
df, meta = read_sas("data/adam/ADSL.sas7bdat")

# Handle SAS missing values
df = handle_sas_missing(df)

# Convert SAS dates to Python dates
df = convert_sas_dates(df, ["RFSTDTC", "RFENDTC"])
```

#### Comparing Datasets

```python
from sas2py.compare.macros import compvars, complibs, compare

# Compare variables between datasets
base_df, _ = read_sas("data/adam/ADSL.sas7bdat")
comp_df, _ = read_sas("data/adam/mod_01/ADSL.sas7bdat")
vars_left, vars_right, vars_both = compvars(base_df, comp_df)

# Compare datasets with BY variables
result = compare(base_df, comp_df, by=["USUBJID"], 
                numeric_abs_tol=1.0e-9, numeric_rel_tol=1.0e-6)
```

#### Generating PhUSE Box Plots

```python
from sas2py.phuse.boxplot import generate_phuse_boxplots

# Generate box plots for ALB parameter
figures = generate_phuse_boxplots(
    input_file="data/adam/ADLBC.sas7bdat",
    output_dir="results/phuse_boxplots",
    parameters=["ALB"],
    visits=[0, 2, 4, 6],
    file_format="html"
)
```

## Package Structure

```
src/sas2py/
├── __init__.py
├── core/              # Core SAS dataset handling
│   ├── __init__.py
│   └── readers.py     # SAS dataset reading utilities
├── compare/           # Dataset comparison utilities
│   ├── __init__.py
│   ├── cli.py         # Command-line interface
│   └── macros.py      # SAS macro implementations
├── phuse/             # PhUSE visualization utilities
│   ├── __init__.py
│   ├── boxplot.py     # Box plot generation
│   ├── cli.py         # Command-line interface
│   └── utils.py       # Utility functions
└── utils/             # General utilities
    ├── __init__.py
    └── test_helpers.py # Testing utilities
```

## Migration Notes

This package implements Python equivalents of:

1. **PHUSE Box Plot Workflow**:
   - Original: `programs/example_phuse_whitepapers/WPCT-F.07.01.sas`
   - Migrated: `src/sas2py/phuse/boxplot.py`

2. **Dataset Comparison Utilities**:
   - Original: `programs/example_compare/test_compare_macros.sas`
   - Migrated: `src/sas2py/compare/macros.py`

See `docs/` directory for detailed mapping of SAS to Python translations.

## Testing

Run the tests to verify parity with SAS outputs:

```bash
# Run all tests
pytest

# Run parity tests specifically
pytest tests/parity/
```

## License

MIT License
