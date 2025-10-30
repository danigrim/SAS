#!/usr/bin/env python
"""
Dataset Comparison CLI Script
Compares SAS datasets for quality control validation
"""
import argparse
import os
import sys
import logging
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sas2py.compare.macros import compvars, complibs, compare
from src.sas2py.core.readers import read_sas

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare SAS datasets")
    subparsers = parser.add_subparsers(dest="command", help="Comparison command to run")
    
    compvars_parser = subparsers.add_parser("compvars", help="Compare variables in two datasets")
    compvars_parser.add_argument("base", help="Path to base dataset")
    compvars_parser.add_argument("comp", help="Path to comparison dataset")
    compvars_parser.add_argument("--output", help="Output file path (JSON)")
    
    complibs_parser = subparsers.add_parser("complibs", help="Compare all datasets in two libraries")
    complibs_parser.add_argument("base", help="Path to base library directory")
    complibs_parser.add_argument("comp", help="Path to comparison library directory")
    complibs_parser.add_argument("--sortvars", help="Variables to sort by (comma-separated)")
    complibs_parser.add_argument("--output", help="Output file path (JSON)")
    
    compare_parser = subparsers.add_parser("compare", help="Compare two datasets in detail")
    compare_parser.add_argument("base", help="Path to base dataset")
    compare_parser.add_argument("comp", help="Path to comparison dataset")
    compare_parser.add_argument("--by", help="Variables to match observations by (comma-separated)")
    compare_parser.add_argument("--abs-tol", type=float, default=1.0e-9, 
                               help="Absolute tolerance for numeric comparisons")
    compare_parser.add_argument("--rel-tol", type=float, default=1.0e-6,
                               help="Relative tolerance for numeric comparisons")
    compare_parser.add_argument("--output", help="Output file path (JSON)")
    
    args = parser.parse_args()
    
    if args.command == "compvars":
        try:
            base_df, _ = read_sas(args.base)
            comp_df, _ = read_sas(args.comp)
            
            vars_left, vars_right, vars_both = compvars(base_df, comp_df)
            
            result = {
                "vars_in_base_only": vars_left,
                "vars_in_comp_only": vars_right,
                "vars_in_both": vars_both
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                print(json.dumps(result, indent=2))
                
        except Exception as e:
            logger.error(f"Error comparing variables: {e}")
            sys.exit(1)
    
    elif args.command == "complibs":
        try:
            sortvars = args.sortvars.split(',') if args.sortvars else None
            
            results = complibs(args.base, args.comp, sortvars)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
            else:
                print(json.dumps(results, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Error comparing libraries: {e}")
            sys.exit(1)
    
    elif args.command == "compare":
        try:
            base_df, _ = read_sas(args.base)
            comp_df, _ = read_sas(args.comp)
            
            by_vars = args.by.split(',') if args.by else None
            
            result = compare(base_df, comp_df, by=by_vars, 
                           numeric_abs_tol=args.abs_tol, 
                           numeric_rel_tol=args.rel_tol)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Error comparing datasets: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)
