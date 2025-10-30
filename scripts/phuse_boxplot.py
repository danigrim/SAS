#!/usr/bin/env python
"""
PhUSE Box Plot Generation CLI Script
Generates box plots for clinical data following PhUSE standards
"""
import argparse
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sas2py.phuse.boxplot import generate_phuse_boxplots

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PhUSE-compliant box plots")
    parser.add_argument("input", help="Path to input SAS dataset (.sas7bdat)")
    parser.add_argument("--output-dir", help="Directory to save output files")
    parser.add_argument("--parameters", required=True, 
                       help="Parameter codes to process (comma-separated)")
    parser.add_argument("--visits", help="Visit numbers to include (comma-separated)")
    parser.add_argument("--measure-var", default="AVAL", 
                       help="Column name for measured value")
    parser.add_argument("--low-var", default="A1LO", 
                       help="Column name for lower limit of normal range")
    parser.add_argument("--high-var", default="A1HI", 
                       help="Column name for upper limit of normal range")
    parser.add_argument("--visit-var", default="AVISITN", 
                       help="Column name for visit/timepoint numeric value")
    parser.add_argument("--visit-label-var", default="AVISIT", 
                       help="Column name for visit/timepoint label")
    parser.add_argument("--treatment-var", default="TRTP", 
                       help="Column name for treatment group")
    parser.add_argument("--population-flag", default="SAFFL", 
                       help="Column name for population flag")
    parser.add_argument("--analysis-flag", default="ANL01FL", 
                       help="Column name for analysis flag")
    parser.add_argument("--reference-lines", default="UNIFORM", 
                       choices=["NONE", "UNIFORM", "NARROW", "ALL"], 
                       help="Type of reference lines")
    parser.add_argument("--max-boxes-per-page", type=int, default=20, 
                       help="Maximum number of boxes per page")
    parser.add_argument("--file-format", default="html", choices=["html", "png", "pdf"], 
                       help="Output file format")
    
    args = parser.parse_args()
    
    parameters = [p.strip() for p in args.parameters.split(',')]
    visits = [int(v.strip()) for v in args.visits.split(',')] if args.visits else None
    
    try:
        figures = generate_phuse_boxplots(
            input_file=args.input,
            output_dir=args.output_dir,
            parameters=parameters,
            visits=visits,
            measure_var=args.measure_var,
            low_var=args.low_var,
            high_var=args.high_var,
            visit_var=args.visit_var,
            visit_label_var=args.visit_label_var,
            treatment_var=args.treatment_var,
            population_flag=args.population_flag,
            analysis_flag=args.analysis_flag,
            reference_lines_type=args.reference_lines,
            max_boxes_per_page=args.max_boxes_per_page,
            file_format=args.file_format
        )
        
        logger.info(f"Generated {len(figures)} box plot figures")
        
        if args.output_dir:
            logger.info(f"Box plots saved to: {args.output_dir}")
        else:
            logger.info("No output directory specified. Plots not saved.")
            
    except Exception as e:
        logger.error(f"Error generating box plots: {e}")
        sys.exit(1)
