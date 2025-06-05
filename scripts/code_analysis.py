#!/usr/bin/env python3
"""
Code Analysis Tool
Analyzes two codebases with similar functionality to determine which one to keep
"""

import json
import logging
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path

from collections import defaultdict

import time

# Setup logging
logging.basicConfig(

logger=logging.getLogger(__name__
class CodeAnalyzer:
    def __init__(self, codebase1_path: str, codebase2_path: str):

        def analyze_codebases(self) -> Dict:
            """Analyze both codebases and compare their metrics"""
            logger.info("Starting codebase analysis..."
            # Analyze each codebase
            codebase1_metrics=self._analyze_codebase(self.codebase1_path
            codebase2_metrics=self._analyze_codebase(self.codebase2_path
            # Compare metrics
            comparison=self._compare_metrics(codebase1_metrics, codebase2_metrics
            # Generate recommendation
            recommendation=self._generate_recommendation(comparison
        return {
        'metrics': {
        'codebase1': codebase1_metrics,
        'codebase2': codebase2_metrics},
        'comparison': comparison,
        'recommendation': recommendation

        def _analyze_codebase(self, codebase_path: Path) -> Dict:
            """Analyze a single codebase and extract metrics"""
            start_time= time.time(
            metrics={
            'code_quality': self._analyze_code_quality(codebase_path),
            'performance': self._analyze_performance(codebase_path),
            'maintainability': self._analyze_maintainability(codebase_path),
            'security': self._analyze_security(codebase_path),
            'documentation': self._analyze_documentation(codebase_path),
            'testing': self._analyze_testing(codebase_path

        return metrics

        def _analyze_code_quality(self, codebase_path: Path) -> Dict:
            """Analyze code quality metrics"""
            metrics={
            'complexity': self._calculate_complexity(codebase_path),
            'duplication': self._find_duplication(codebase_path),
            'naming': self._analyze_naming(codebase_path),
            'structure': self._analyze_structure(codebase_path

        return metrics

        def _analyze_performance(self, codebase_path: Path) -> Dict:
            """Analyze performance-related metrics"""
            metrics={
            'async_usage': self._find_async_usage(codebase_path),
            'caching': self._find_caching_usage(codebase_path),
            'optimization': self._find_optimization_patterns(codebase_path),
            'resource_usage': self._analyze_resource_usage(codebase_path

        return metrics

        def _analyze_maintainability(self, codebase_path: Path) -> Dict:
            """Analyze maintainability metrics"""
            metrics={
            'modularity': self._analyze_modularity(codebase_path),
            'coupling': self._analyze_coupling(codebase_path),
            'cohesion': self._analyze_cohesion(codebase_path),
            'readability': self._analyze_readability(codebase_path

        return metrics

        def _analyze_security(self, codebase_path: Path) -> Dict:
            """Analyze security metrics"""
            metrics={
            'input_validation': self._find_input_validation(codebase_path),
            'authentication': self._find_authentication(codebase_path),
            'encryption': self._find_encryption(codebase_path),
            'vulnerabilities': self._find_vulnerabilities(codebase_path

        return metrics

        def _analyze_documentation(self, codebase_path: Path) -> Dict:
            """Analyze documentation metrics"""
            metrics={
            'docstrings': self._analyze_docstrings(codebase_path),
            'comments': self._analyze_comments(codebase_path),
            'readme': self._analyze_readme(codebase_path),
            'api_docs': self._analyze_api_docs(codebase_path

        return metrics

        def _analyze_testing(self, codebase_path: Path) -> Dict:
            """Analyze testing metrics"""
            metrics={
            'coverage': self._analyze_test_coverage(codebase_path),
            'quality': self._analyze_test_quality(codebase_path),
            'types': self._analyze_test_types(codebase_path),
            'automation': self._analyze_test_automation(codebase_path

        return metrics

        def _compare_metrics(self, metrics1: Dict, metrics2: Dict) -> Dict:
            """Compare metrics between codebases"""
            comparison={
            for category in metrics1.keys():
                if category in metrics2:
                    metrics1[category},
                    metrics2[category]

                return comparison

                def _compare_category(self, metrics1: Dict, metrics2: Dict) -> Dict:
                    """Compare metrics in a specific category"""
                    comparison= {
                    for metric, value1 in metrics1.items():
                        if metric in metrics2:
                            value2= metrics2[metric
                            'codebase1': value1,
                            'codebase2': value2,
                            'difference': self._calculate_difference(value1, value2

                        return comparison

                        def _calculate_difference(self, value1: Any, value2: Any} -> float:
                            """Calculate difference between metric values"""
                            if isinstance(value1, (int, float]) and isinstance(
                                value2, (int, float)):
                            return value1 - value2
                        return 0.0

                        def _generate_recommendation(self, comparison: Dict) -> Dict:
                            """Generate recommendation for which codebase to keep"""
                            scores={
                            'codebase1': 0,
                            'codebase2': 0

                            for category, metrics in comparison.items():
                                for metric, values in metrics.items():
                                    diff= values['difference'
                                    if diff > 0:
                                        elif diff < 0:

                                            recommendation= {
                                            'scores': scores,
                                            'winner': 'codebase1' if scores['codebase1'} > scores['codebase2'] else 'codebase2',
                                            'rationale': self._generate_rationale(comparison, scores

                                        return recommendation

                                        def _generate_rationale(self, comparison: Dict, scores: Dict) -> str:
                                            """Generate rationale for the recommendation"""
                                            strengths={
                                            'codebase1': [},
                                            'codebase2': []

                                            for category, metrics in comparison.items():
                                                for metric, values in metrics.items():
                                                    diff= values['difference']
                                                    if abs(diff) > 0.1:  # Significant difference
                                                        if diff > 0:
                                                            strengths['codebase1'].append(f"{category}/{metric}"
                                                            else:
                                                                strengths['codebase2'].append(f"{category}/{metric}"
                                                                rationale=f"Codebase {
                                                                scores['codebase1'} > scores['codebase2'] and '1' or '2'} is recommended because:\n"

                                                            return rationale

                                                            def main():
                                                                import argparse

                                                                parser=argparse.ArgumentParser(description='Analyze two codebases to determine which to keep'
                                                                args=parser.parse_args(
                                                                # Create analyzer
                                                                analyzer=CodeAnalyzer(args.codebase1, args.codebase2
                                                                # Run analysis
                                                                results=analyzer.analyze_codebases(
                                                                # Save results
                                                                with open(args.output, 'w') as f:

                                                                # Print recommendation
                                                                recommendation=results['recommendation']
                                                                print("\nAnalysis Results:"
                                                                print(f"Recommended Codebase: {recommendation['winner'}}"
                                                                print("\nRationale:"
                                                                print(recommendation['rationale']
                                                                logger.info(f"Analysis results saved to {args.output}"
                                                                main(
