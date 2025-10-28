# Simple Demographics Summary Example

This example demonstrates a basic SAS-to-Python migration pattern for clinical trial demographic analysis.

## SAS Program

**File:** `demographics_summary.sas`

**Purpose:** Calculate demographic summary statistics by treatment group

**SAS Operations:**
- `PROC MEANS` - Calculate age statistics (N, MEAN, STD, MIN, MAX) by treatment
- `PROC FREQ` - Count subjects by treatment and sex

**Input:** ADSL dataset (Subject-Level Analysis Dataset)

**Output:** Summary statistics printed to SAS output window

## Python Migration

**File:** `../../airflow_migration/scripts/demographics_summary.py`

**Purpose:** Same analysis using PySpark

**Key Mappings:**

| SAS | Python/PySpark |
|-----|----------------|
| `PROC MEANS ... CLASS trt01p; VAR age;` | `df.groupBy("trt01p").agg(mean("age"), stddev("age"), ...)` |
| `PROC FREQ ... TABLES trt01p*sex;` | `df.groupBy("trt01p", "sex").agg(count("usubjid"))` |
| `LIBNAME adam "path";` | `spark.read.format("com.github.saurfang.sas.spark").load(path)` |

## Running the Analysis

### SAS Version
```sas
%include "programs/example_simple/demographics_summary.sas";
```

### Python Version
```bash
cd airflow_migration/scripts
python demographics_summary.py
```

## Expected Output

The analysis produces:
1. Age statistics by treatment group (N, mean, std, min, max)
2. Subject counts by treatment group and sex

Both SAS and Python versions should produce equivalent results (within floating-point precision).

## Migration Patterns Demonstrated

This simple example demonstrates several key SAS-to-Python migration patterns:

1. **Data Access**: Converting `LIBNAME` statements to PySpark data readers
2. **Aggregation**: Converting `PROC MEANS` to `groupBy().agg()` operations
3. **Frequency Tables**: Converting `PROC FREQ` to `groupBy().count()` operations
4. **Statistical Functions**: Mapping SAS statistical functions to PySpark equivalents

See the comprehensive migration guide at `airflow_migration/docs/sas_to_pyspark_mapping.md` for more patterns.
