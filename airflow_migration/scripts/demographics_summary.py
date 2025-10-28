"""
Demographics Summary Analysis - Python Migration

This script demonstrates migrating a simple SAS PROC MEANS and PROC FREQ
analysis to PySpark. It calculates demographic summary statistics by
treatment group.

SAS equivalent: programs/example_simple/demographics_summary.sas
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import count, mean, stddev, min as spark_min, max as spark_max, col
import os


def create_spark_session(app_name="DemographicsSummary"):
    """Create and return a Spark session."""
    return SparkSession.builder \
        .appName(app_name) \
        .getOrCreate()


def read_adsl_dataset(spark, data_path):
    """
    Read ADSL dataset from SAS format.
    
    Equivalent to: LIBNAME adam "../../data/adam"; DATA adsl; SET adam.adsl; RUN;
    
    Args:
        spark: SparkSession object
        data_path: Path to the ADSL dataset
    
    Returns:
        PySpark DataFrame containing ADSL data
    """
    df = spark.read.format("com.github.saurfang.sas.spark") \
        .load(data_path)
    return df


def calculate_age_statistics(df):
    """
    Calculate age summary statistics by treatment group.
    
    Equivalent to SAS:
        PROC MEANS DATA=adam.adsl N MEAN STD MIN MAX;
            CLASS trt01p;
            VAR age;
        RUN;
    
    Args:
        df: PySpark DataFrame with ADSL data
    
    Returns:
        DataFrame with summary statistics
    """
    stats_df = df.groupBy("trt01p") \
        .agg(
            count("usubjid").alias("n"),
            mean("age").alias("mean_age"),
            stddev("age").alias("std_age"),
            spark_min("age").alias("min_age"),
            spark_max("age").alias("max_age")
        ) \
        .orderBy("trt01p")
    
    return stats_df


def count_subjects_by_treatment_sex(df):
    """
    Count subjects by treatment group and sex.
    
    Equivalent to SAS:
        PROC FREQ DATA=adam.adsl;
            TABLES trt01p*sex;
        RUN;
    
    Args:
        df: PySpark DataFrame with ADSL data
    
    Returns:
        DataFrame with subject counts
    """
    freq_df = df.groupBy("trt01p", "sex") \
        .agg(count("usubjid").alias("n_subjects")) \
        .orderBy("trt01p", "sex")
    
    return freq_df


def save_results(stats_df, freq_df, output_path):
    """Save analysis results to parquet files."""
    os.makedirs(output_path, exist_ok=True)
    
    stats_df.write.mode("overwrite").parquet(
        os.path.join(output_path, "age_statistics.parquet")
    )
    
    freq_df.write.mode("overwrite").parquet(
        os.path.join(output_path, "treatment_sex_counts.parquet")
    )
    
    print(f"Results saved to {output_path}")


def main():
    """Main execution function."""
    spark = create_spark_session()
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "..", "data", "adam", "adsl.sas7bdat")
    output_path = os.path.join(base_path, "..", "results", "demographics_summary")
    
    print("=" * 80)
    print("Demographic Summary: Age by Treatment Group")
    print("=" * 80)
    
    print("\n1. Reading ADSL dataset...")
    adsl_df = read_adsl_dataset(spark, data_path)
    print(f"   Total subjects: {adsl_df.count()}")
    
    print("\n2. Calculating age statistics by treatment group...")
    stats_df = calculate_age_statistics(adsl_df)
    print("\nAge Statistics:")
    stats_df.show()
    
    print("\n3. Counting subjects by treatment and sex...")
    freq_df = count_subjects_by_treatment_sex(adsl_df)
    print("\nSubject Count by Treatment and Sex:")
    freq_df.show()
    
    print("\n4. Saving results...")
    save_results(stats_df, freq_df, output_path)
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)
    
    spark.stop()


if __name__ == "__main__":
    main()
