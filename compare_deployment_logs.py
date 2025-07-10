#!/usr/bin/env python3
"""
Deployment Log Comparison Tool
===============================
Helps compare working vs broken deployment logs to identify root causes.
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any

class DeploymentLogAnalyzer:
    """Analyze deployment logs for patterns and issues"""
    
    def __init__(self):
        self.patterns = {
            'errors': [
                r'ERROR',
                r'error',
                r'failed',
                r'Failed',
                r'exception',
                r'Exception',
                r'traceback',
                r'Traceback',
                r'CRITICAL',
                r'500',
                r'502',
                r'503',
                r'504'
            ],
            'warnings': [
                r'WARNING',
                r'warning',
                r'WARN',
                r'deprecated',
                r'Deprecated'
            ],
            'success': [
                r'SUCCESS',
                r'success',
                r'✅',
                r'completed',
                r'Completed',
                r'started',
                r'Started',
                r'ready',
                r'Ready'
            ],
            'deployment_stages': [
                r'Building',
                r'Deploying',
                r'Starting',
                r'Health check',
                r'Live',
                r'Failed'
            ]
        }
    
    def analyze_log_file(self, log_file_path: str) -> Dict[str, Any]:
        """Analyze a single log file"""
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'file': log_file_path,
                'total_lines': len(content.split('\n')),
                'errors': [],
                'warnings': [],
                'success_indicators': [],
                'deployment_stages': [],
                'timestamps': [],
                'unique_errors': set(),
                'api_endpoints': [],
                'component_status': {}
            }
            
            for line_num, line in enumerate(content.split('\n'), 1):
                # Extract timestamps
                timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', line)
                if timestamp_match:
                    analysis['timestamps'].append({
                        'line': line_num,
                        'timestamp': timestamp_match.group(),
                        'content': line.strip()
                    })
                
                # Find errors
                for pattern in self.patterns['errors']:
                    if re.search(pattern, line, re.IGNORECASE):
                        analysis['errors'].append({
                            'line': line_num,
                            'pattern': pattern,
                            'content': line.strip()
                        })
                        analysis['unique_errors'].add(line.strip())
                
                # Find warnings
                for pattern in self.patterns['warnings']:
                    if re.search(pattern, line, re.IGNORECASE):
                        analysis['warnings'].append({
                            'line': line_num,
                            'pattern': pattern,
                            'content': line.strip()
                        })
                
                # Find success indicators
                for pattern in self.patterns['success']:
                    if re.search(pattern, line, re.IGNORECASE):
                        analysis['success_indicators'].append({
                            'line': line_num,
                            'pattern': pattern,
                            'content': line.strip()
                        })
                
                # Find deployment stages
                for pattern in self.patterns['deployment_stages']:
                    if re.search(pattern, line, re.IGNORECASE):
                        analysis['deployment_stages'].append({
                            'line': line_num,
                            'stage': pattern,
                            'content': line.strip()
                        })
                
                # Find API endpoints
                api_match = re.search(r'/api/v\d+/[\w\-/]+', line)
                if api_match:
                    analysis['api_endpoints'].append({
                        'line': line_num,
                        'endpoint': api_match.group(),
                        'content': line.strip()
                    })
                
                # Component status
                if 'component' in line.lower() or 'status' in line.lower():
                    analysis['component_status'][line_num] = line.strip()
            
            return analysis
            
        except Exception as e:
            return {
                'file': log_file_path,
                'error': str(e)
            }
    
    def compare_logs(self, working_log_path: str, broken_log_path: str) -> Dict[str, Any]:
        """Compare two deployment logs"""
        working_analysis = self.analyze_log_file(working_log_path)
        broken_analysis = self.analyze_log_file(broken_log_path)
        
        comparison = {
            'working_log': working_analysis,
            'broken_log': broken_analysis,
            'differences': {
                'new_errors': [],
                'missing_success_indicators': [],
                'deployment_stage_differences': [],
                'timing_differences': [],
                'component_differences': []
            }
        }
        
        # Find new errors in broken log
        working_errors = set(item['content'] for item in working_analysis.get('errors', []))
        broken_errors = set(item['content'] for item in broken_analysis.get('errors', []))
        comparison['differences']['new_errors'] = list(broken_errors - working_errors)
        
        # Find missing success indicators
        working_success = set(item['content'] for item in working_analysis.get('success_indicators', []))
        broken_success = set(item['content'] for item in broken_analysis.get('success_indicators', []))
        comparison['differences']['missing_success_indicators'] = list(working_success - broken_success)
        
        # Compare deployment stages
        working_stages = [item['stage'] for item in working_analysis.get('deployment_stages', [])]
        broken_stages = [item['stage'] for item in broken_analysis.get('deployment_stages', [])]
        comparison['differences']['deployment_stage_differences'] = {
            'working_only': list(set(working_stages) - set(broken_stages)),
            'broken_only': list(set(broken_stages) - set(working_stages))
        }
        
        return comparison
    
    def generate_report(self, comparison: Dict[str, Any]) -> str:
        """Generate a human-readable comparison report"""
        report = []
        report.append("=" * 80)
        report.append("DEPLOYMENT LOG COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        working = comparison['working_log']
        broken = comparison['broken_log']
        
        report.append("SUMMARY:")
        report.append(f"  Working log: {working.get('file', 'N/A')}")
        report.append(f"    - Total lines: {working.get('total_lines', 0)}")
        report.append(f"    - Errors: {len(working.get('errors', []))}")
        report.append(f"    - Warnings: {len(working.get('warnings', []))}")
        report.append(f"    - Success indicators: {len(working.get('success_indicators', []))}")
        report.append("")
        
        report.append(f"  Broken log: {broken.get('file', 'N/A')}")
        report.append(f"    - Total lines: {broken.get('total_lines', 0)}")
        report.append(f"    - Errors: {len(broken.get('errors', []))}")
        report.append(f"    - Warnings: {len(broken.get('warnings', []))}")
        report.append(f"    - Success indicators: {len(broken.get('success_indicators', []))}")
        report.append("")
        
        # Key differences
        diff = comparison['differences']
        
        if diff['new_errors']:
            report.append("NEW ERRORS IN BROKEN DEPLOYMENT:")
            for error in diff['new_errors'][:10]:  # Show first 10
                report.append(f"  ❌ {error}")
            if len(diff['new_errors']) > 10:
                report.append(f"  ... and {len(diff['new_errors']) - 10} more")
            report.append("")
        
        if diff['missing_success_indicators']:
            report.append("MISSING SUCCESS INDICATORS:")
            for success in diff['missing_success_indicators'][:10]:
                report.append(f"  ⚠️ {success}")
            if len(diff['missing_success_indicators']) > 10:
                report.append(f"  ... and {len(diff['missing_success_indicators']) - 10} more")
            report.append("")
        
        if diff['deployment_stage_differences']['broken_only']:
            report.append("DEPLOYMENT STAGES ONLY IN BROKEN:")
            for stage in diff['deployment_stage_differences']['broken_only']:
                report.append(f"  🔴 {stage}")
            report.append("")
        
        if diff['deployment_stage_differences']['working_only']:
            report.append("DEPLOYMENT STAGES ONLY IN WORKING:")
            for stage in diff['deployment_stage_differences']['working_only']:
                report.append(f"  🟢 {stage}")
            report.append("")
        
        report.append("=" * 80)
        report.append("RECOMMENDATIONS:")
        report.append("1. Focus on the 'NEW ERRORS' section - these are likely root causes")
        report.append("2. Check 'MISSING SUCCESS INDICATORS' - these show what broke")
        report.append("3. Compare deployment stages to see where the process differs")
        report.append("4. Look for timing differences in timestamp patterns")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main function to run log comparison"""
    analyzer = DeploymentLogAnalyzer()
    
    print("=" * 60)
    print("DEPLOYMENT LOG COMPARISON TOOL")
    print("=" * 60)
    print()
    
    print("This tool helps you compare working vs broken deployment logs.")
    print("You need to:")
    print("1. Download logs from Digital Ocean App Platform")
    print("2. Save them as text files")
    print("3. Run this comparison")
    print()
    
    print("HOW TO GET DEPLOYMENT LOGS:")
    print("1. Go to: https://cloud.digitalocean.com/apps")
    print("2. Click your app → Activity tab")
    print("3. Find a WORKING deployment → Click it → Copy logs")
    print("4. Save as 'working_deployment.log'")
    print("5. Find a BROKEN deployment → Click it → Copy logs")
    print("6. Save as 'broken_deployment.log'")
    print("7. Run this script again")
    print()
    
    working_log = "working_deployment.log"
    broken_log = "broken_deployment.log"
    
    if not os.path.exists(working_log):
        print(f"❌ Working log file '{working_log}' not found!")
        print("Please download and save your working deployment logs first.")
        return 1
    
    if not os.path.exists(broken_log):
        print(f"❌ Broken log file '{broken_log}' not found!")
        print("Please download and save your broken deployment logs first.")
        return 1
    
    print("🔍 Analyzing logs...")
    comparison = analyzer.compare_logs(working_log, broken_log)
    
    print("📊 Generating report...")
    report = analyzer.generate_report(comparison)
    
    # Save report
    report_file = f"deployment_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_file}")
    print()
    print("=" * 60)
    print("REPORT PREVIEW:")
    print("=" * 60)
    print(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 