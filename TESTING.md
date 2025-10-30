# Testing the SAS to Python Migration

This document describes the testing approach for the SAS to Python migration project, focusing on ensuring parity between SAS and Python outputs.

## Testing Philosophy

The testing strategy follows these core principles:

1. **Truth-first**: All tests are based on actual SAS behavior, not assumed behavior
2. **Determinism**: Random seeds are fixed and rounding behavior is explicit
3. **Auditable**: Side-by-side parity tests with golden fixtures
4. **Like-for-like**: Implementations match before optimizations

## Test Suite Structure

```
tests/
├── __init__.py
├── parity/                 # Parity tests comparing SAS vs Python outputs
│   ├── __init__.py
│   ├── test_dataset_readers.py    # Tests for SAS dataset reading
│   ├── test_comparison_macros.py  # Tests for SAS comparison macros
│   ├── test_boxplot.py            # Tests for PhUSE boxplot generation
│   ├── generate_fixtures.py       # Utility to generate test fixtures
│   └── fixtures/                  # Golden fixture data for testing
│       ├── adsl_sample.csv
│       ├── adsl_base_sample.csv
│       ├── adsl_mod_sample.csv
│       └── adlbc_sample.csv
└── unit/                   # Unit tests (future addition)
```

## Test Categories

### 1. Parity Tests

These tests verify that the Python implementation produces outputs that match SAS outputs within specified tolerances:

- **Dataset Reading Tests**: Verify that SAS datasets are read correctly
- **Comparison Macro Tests**: Test the Python implementation of SAS comparison macros
- **Box Plot Tests**: Test PhUSE box plot generation

### 2. Unit Tests

Unit tests for individual components and functions (to be added in future iterations).

## Running Tests

### Running All Tests

```bash
# Using Poetry
poetry run pytest

# With test output
poetry run pytest -xvs
```

### Running Specific Test Categories

```bash
# Run only parity tests
poetry run pytest tests/parity/

# Run specific test file
poetry run pytest tests/parity/test_dataset_readers.py

# Run a specific test function
poetry run pytest tests/parity/test_dataset_readers.py::TestSASReaders::test_read_sas_adsl
```

## Test Fixtures

Test fixtures are stored in the `tests/parity/fixtures/` directory. These are small, sanitized versions of actual SAS datasets converted to CSV format for testing.

### Generating Test Fixtures

Test fixtures can be regenerated using the `generate_fixtures.py` script:

```bash
poetry run python tests/parity/generate_fixtures.py
```

## Validation Criteria

The following validation criteria are used:

1. **Row Count Parity**: SAS and Python outputs must have identical row counts
2. **Column Structure Parity**: Column names and structures must match
3. **Numeric Value Parity**: Numeric values must be within specified tolerances:
   - Absolute tolerance: 1e-9
   - Relative tolerance: 1e-6
4. **Date/Time Parity**: Date/time values must match exactly after accounting for SAS epoch
5. **Missing Value Handling**: Missing values must be handled consistently
6. **Sort Order**: Sort order must match SAS behavior (missing values first)

## Continuous Integration

Tests are run automatically in GitHub Actions CI for every pull request:

1. **test.yml**: Runs all unit tests on multiple Python versions
2. **parity.yml**: Runs parity tests comparing SAS and Python outputs

See `.github/workflows/` for the CI configuration.

## Test Helpers

Custom test helpers are available in `src/sas2py/utils/test_helpers.py`:

- `assert_frame_equalish`: Compare DataFrames with customizable tolerances
- `generate_test_fixtures`: Generate fixture files from SAS datasets

## Known Test Limitations

1. **PhUSE Box Plot Tests**: Some PhUSE box plot tests are skipped due to implementation differences
2. **Test Data Size**: Test fixtures are small subsets of actual data
3. **Special SAS Features**: Some SAS-specific features may not have tests yet

## Adding New Tests

1. Add a new test file or extend existing test files
2. Follow the pattern of existing tests
3. Ensure deterministic comparison with SAS outputs
4. Use appropriate tolerances for numeric comparisons
