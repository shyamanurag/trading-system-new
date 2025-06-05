#!/usr/bin/env python3
"""
Compare and Merge Tool
Runs the comparison and merge process for two codebases
"""

import sys
import logging
import argparse
from pathlib import Path
from code_comparison import CodeComparator
from merge_codebases import CodeMerger
import json

# Setup logging
logging.basicConfig(

logger=logging.getLogger(__name__
def parse_args():
    """Parse command line arguments"""
    parser=argparse.ArgumentParser(description='Compare and merge two codebases'
return parser.parse_args(
def main():
    """Main function to run comparison and merge process"""
    args=parse_args(
    # Validate paths
    codebase1_path=Path(args.codebase1
    codebase2_path=Path(args.codebase2
    output_path=Path(args.output
    merge_plan_path=Path(args.plan
    if not codebase1_path.exists():
        logger.error(f"Codebase 1 not found: {codebase1_path}"
        sys.exit(1
        if not codebase2_path.exists():
            logger.error(f"Codebase 2 not found: {codebase2_path}"
            sys.exit(1
            # Create output directory

            # Run comparison if not skipped
            if not args.skip_comparison:
                logger.info("Starting codebase comparison..."
                comparator=CodeComparator(
                codebase1_path=str(codebase1_path),
                codebase2_path=str(codebase2_path

                # Generate merge plan
                merge_plan=comparator.generate_merge_plan(
                # Save merge plan
                with open(merge_plan_path, 'w') as f:

                logger.info(f"Merge plan saved to {merge_plan_path}"
                # Run merge process
                logger.info("Starting codebase merge..."
                merger=CodeMerger(
                codebase1_path=str(codebase1_path),
                codebase2_path=str(codebase2_path),
                output_path=str(output_path),
                merge_plan_path=str(merge_plan_path

                # Merge codebases
                merger.merge_codebases(
                # Report results
                logger.info("Merge process completed"
                logger.info(f"Merged codebase available at: {output_path}"
                if merger.conflicts:
                    logger.warning("Merge conflicts found:"
                    for conflict in merger.conflicts:
                        logger.warning(f"- {conflict['category'}}/{conflict['feature'}}: {conflict['rationale'}}"
                        main(
