#!/usr/bin/env python3
"""
Simple Systematic TrueData Validator
Tests TrueData accuracy with web verification and comprehensive reporting
"""

import asyncio
import time
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path
import statistics

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from truedata import TD_live
    TRUEDATA_AVAILABLE = True
    print("✅ TrueData library found")
except ImportError as e:
    TRUEDATA_AVAILABLE = False
    print(f"❌ TrueData library not available: {e}")

class SimpleTrueDataValidator:
    def __init__(self):
        self.td_client = None
        
        # Test symbols - mix of indices and stocks  
        self.test_symbols = [
            "RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK",
            "SBIN", "ITC", "HDFCBANK", "BHARTIARTL", "KOTAKBANK",
            "WIPRO", "LT", "MARUTI", "ASIANPAINT", "NESTLEIND"
        ]
        
        # Real subscription credentials
        self.username = "tdwsp697"
        self.password = "shyam@697"
        self.port = 8084
        
        # Initialize session for web requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def connect_truedata(self) -> bool:
        """Connect to TrueData with real credentials"""
        if not TRUEDATA_AVAILABLE:
            print("❌ TrueData library not available")
            return False
            
        try:
            print(f"🔌 Connecting to TrueData...")
            print(f"   Username: {self.username}")
            print(f"   Port: {self.port}")
            
            self.td_client = TD_live(
                self.username, 
                self.password, 
                live_port=self.port,
                compression=False  # Avoid decompression bug
            )
            
            if self.td_client:
                print("✅ TrueData connected successfully!")
                time.sleep(2)  # Allow connection to stabilize
                return True
            else:
                print("❌ TrueData connection failed")
                return False
                
        except Exception as e:
            print(f"❌ TrueData connection error: {e}")
            return False

    def get_truedata_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get live prices from TrueData"""
        if not self.td_client:
            print("❌ TrueData client not connected")
            return {}
            
        try:
            print(f"📊 Requesting TrueData for {len(symbols)} symbols...")
            
            # Subscribe to symbols one by one
            for symbol in symbols:
                try:
                    # Use the method we know works
                    self.td_client.live_data_request([symbol])
                    print(f"   📡 Subscribed to {symbol}")
                    time.sleep(0.2)  # Small delay between subscriptions
                except Exception as e:
                    print(f"   ❌ Failed to subscribe to {symbol}: {e}")
            
            # Wait for data to populate
            print("   ⏳ Waiting for data...")
            time.sleep(5)  # Give more time for data
            
            # Get live data
            print("   📦 Retrieving live data...")
            raw_data = self.td_client.get_live_data()
            
            if raw_data:
                print(f"   ✅ Received data: {len(raw_data)} items")
                print(f"   📋 Sample data: {raw_data[:2] if len(raw_data) >= 2 else raw_data}")
            else:
                print("   ❌ No data received")
                return {}
            
            # Parse TrueData response format
            parsed_data = {}
            if isinstance(raw_data, list):
                for item in raw_data:
                    if isinstance(item, list) and len(item) >= 6:
                        try:
                            symbol = item[0]
                            timestamp = item[2] if len(item) > 2 else None
                            prev_close = float(item[3]) if len(item) > 3 and item[3] else None
                            change = float(item[4]) if len(item) > 4 and item[4] else None
                            ltp = float(item[5]) if len(item) > 5 and item[5] else None
                            volume = int(item[6]) if len(item) > 6 and item[6] else None
                            
                            if ltp and ltp > 0:  # Valid price
                                parsed_data[symbol] = {
                                    'price': ltp,
                                    'timestamp': timestamp,
                                    'prev_close': prev_close,
                                    'change': change,
                                    'volume': volume,
                                    'raw_data': item
                                }
                                print(f"   ✅ {symbol}: ₹{ltp:,.2f}")
                        except Exception as e:
                            print(f"   ❌ Error parsing data for item: {e}")
                            continue
                            
            print(f"   📊 Successfully parsed {len(parsed_data)} symbols")
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error getting TrueData prices: {e}")
            return {}

    async def get_yahoo_price(self, symbol: str) -> Optional[float]:
        """Get price from Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    if 'meta' in result and 'regularMarketPrice' in result['meta']:
                        return float(result['meta']['regularMarketPrice'])
                        
        except Exception as e:
            print(f"   ❌ Yahoo Finance error for {symbol}: {e}")
        return None

    async def get_google_price(self, symbol: str) -> Optional[float]:
        """Get price from Google Finance (alternative source)"""
        try:
            # Google Finance doesn't have a direct API, but we can try NSE directly
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.nseindia.com/'
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'priceInfo' in data and 'lastPrice' in data['priceInfo']:
                    return float(data['priceInfo']['lastPrice'])
                    
        except Exception as e:
            print(f"   ❌ NSE API error for {symbol}: {e}")
        return None

    def calculate_accuracy_metrics(self, truedata_price: float, web_prices: Dict[str, float]) -> Dict:
        """Calculate comprehensive accuracy metrics"""
        if not web_prices:
            return {'status': 'no_web_data'}
            
        metrics = {
            'truedata_price': truedata_price,
            'web_prices': web_prices,
            'comparisons': {},
            'status': 'calculated'
        }
        
        differences = []
        percentage_differences = []
        
        for source, web_price in web_prices.items():
            diff = abs(truedata_price - web_price)
            pct_diff = (diff / web_price) * 100 if web_price > 0 else 100
            
            differences.append(diff)
            percentage_differences.append(pct_diff)
            
            # Accuracy grade
            if pct_diff <= 0.1:
                grade = "A+ (Excellent)"
            elif pct_diff <= 0.5:
                grade = "A (Very Good)"
            elif pct_diff <= 1.0:
                grade = "B (Good)"
            elif pct_diff <= 2.0:
                grade = "C (Fair)"
            else:
                grade = "D (Poor)"
                
            metrics['comparisons'][source] = {
                'web_price': web_price,
                'difference': diff,
                'percentage_difference': pct_diff,
                'accuracy_grade': grade
            }
        
        # Overall metrics
        if percentage_differences:
            metrics['average_percentage_difference'] = statistics.mean(percentage_differences)
            metrics['max_percentage_difference'] = max(percentage_differences)
            metrics['min_percentage_difference'] = min(percentage_differences)
            
            avg_diff = metrics['average_percentage_difference']
            if avg_diff <= 0.1:
                metrics['overall_grade'] = "A+ (Excellent)"
            elif avg_diff <= 0.5:
                metrics['overall_grade'] = "A (Very Good)"
            elif avg_diff <= 1.0:
                metrics['overall_grade'] = "B (Good)"
            elif avg_diff <= 2.0:
                metrics['overall_grade'] = "C (Fair)"
            else:
                metrics['overall_grade'] = "D (Poor)"
        
        return metrics

    async def validate_symbol(self, symbol: str, truedata_data: Dict) -> Dict:
        """Validate a single symbol against web sources"""
        print(f"\n🔍 Validating {symbol}...")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Check if TrueData is available
        if symbol not in truedata_data:
            result['status'] = 'no_truedata'
            result['error'] = 'Symbol not found in TrueData response'
            print(f"   ❌ No TrueData available for {symbol}")
            return result
            
        truedata_info = truedata_data[symbol]
        truedata_price = truedata_info['price']
        result['truedata_data'] = truedata_info
        
        print(f"   💰 TrueData Price: ₹{truedata_price:,.2f}")
        
        # Get web prices from multiple sources
        web_prices = {}
        
        # Yahoo Finance
        print(f"   📡 Fetching Yahoo Finance price...")
        yahoo_price = await self.get_yahoo_price(symbol)
        if yahoo_price:
            web_prices['Yahoo Finance'] = yahoo_price
            print(f"   🌐 Yahoo Finance: ₹{yahoo_price:,.2f}")
        
        # NSE API
        print(f"   📡 Fetching NSE API price...")
        nse_price = await self.get_google_price(symbol)
        if nse_price:
            web_prices['NSE API'] = nse_price
            print(f"   🌐 NSE API: ₹{nse_price:,.2f}")
        
        # Add delay between sources
        await asyncio.sleep(1)
        
        result['web_prices'] = web_prices
        
        if not web_prices:
            result['status'] = 'no_web_data'
            result['warning'] = 'No web prices available for comparison'
            print(f"   ⚠️  No web data available for comparison")
            return result
            
        # Calculate accuracy metrics
        metrics = self.calculate_accuracy_metrics(truedata_price, web_prices)
        result['accuracy_metrics'] = metrics
        result['status'] = 'completed'
        
        # Print summary
        if 'overall_grade' in metrics:
            print(f"   📊 Overall Grade: {metrics['overall_grade']}")
            print(f"   📈 Avg Difference: {metrics['average_percentage_difference']:.3f}%")
        
        return result

    async def run_systematic_validation(self) -> Dict:
        """Run comprehensive systematic validation"""
        print("🚀 SYSTEMATIC TRUEDATA VALIDATION FRAMEWORK")
        print("="*70)
        print(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"📊 Testing {len(self.test_symbols)} symbols")
        print("="*70)
        
        validation_results = {
            'start_time': datetime.now().isoformat(),
            'symbols_tested': self.test_symbols.copy(),
            'results': [],
            'summary': {},
            'status': 'running'
        }
        
        # Step 1: Connect to TrueData
        print("\n📍 STEP 1: Connecting to TrueData")
        if not self.connect_truedata():
            validation_results['status'] = 'failed'
            validation_results['error'] = 'TrueData connection failed'
            return validation_results
            
        # Step 2: Get TrueData prices
        print("\n📍 STEP 2: Fetching TrueData Prices")
        truedata_data = self.get_truedata_prices(self.test_symbols)
        
        if not truedata_data:
            validation_results['status'] = 'failed'
            validation_results['error'] = 'No TrueData data received'
            return validation_results
            
        print(f"✅ Successfully received TrueData for {len(truedata_data)} symbols")
        
        # Step 3: Validate each symbol
        print("\n📍 STEP 3: Cross-Validation with Web Sources")
        for i, symbol in enumerate(self.test_symbols, 1):
            try:
                print(f"\n--- Symbol {i}/{len(self.test_symbols)} ---")
                result = await self.validate_symbol(symbol, truedata_data)
                validation_results['results'].append(result)
                
                # Rate limiting between symbols
                if i < len(self.test_symbols):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error validating {symbol}: {e}")
                validation_results['results'].append({
                    'symbol': symbol,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Step 4: Generate comprehensive summary
        print("\n📍 STEP 4: Generating Summary")
        validation_results['summary'] = self._generate_comprehensive_summary(validation_results['results'])
        validation_results['end_time'] = datetime.now().isoformat()
        validation_results['status'] = 'completed'
        
        return validation_results

    def _generate_comprehensive_summary(self, results: List[Dict]) -> Dict:
        """Generate comprehensive validation summary"""
        total_symbols = len(results)
        completed_validations = len([r for r in results if r.get('status') == 'completed'])
        truedata_available = len([r for r in results if r.get('truedata_data')])
        web_data_available = len([r for r in results if r.get('web_prices')])
        
        summary = {
            'total_symbols_tested': total_symbols,
            'truedata_symbols_available': truedata_available,
            'web_data_symbols_available': web_data_available,
            'completed_validations': completed_validations,
            'truedata_availability_rate': (truedata_available / total_symbols * 100) if total_symbols > 0 else 0,
            'web_data_availability_rate': (web_data_available / total_symbols * 100) if total_symbols > 0 else 0,
            'success_rate': (completed_validations / total_symbols * 100) if total_symbols > 0 else 0
        }
        
        # Accuracy analysis
        accuracy_differences = []
        accuracy_grades = []
        
        for result in results:
            if result.get('status') == 'completed' and 'accuracy_metrics' in result:
                metrics = result['accuracy_metrics']
                if 'average_percentage_difference' in metrics:
                    accuracy_differences.append(metrics['average_percentage_difference'])
                if 'overall_grade' in metrics:
                    accuracy_grades.append(metrics['overall_grade'])
        
        if accuracy_differences:
            summary['accuracy_analysis'] = {
                'total_accurate_validations': len(accuracy_differences),
                'average_percentage_difference': statistics.mean(accuracy_differences),
                'max_percentage_difference': max(accuracy_differences),
                'min_percentage_difference': min(accuracy_differences),
                'median_percentage_difference': statistics.median(accuracy_differences)
            }
            
            # Grade distribution
            grade_counts = {}
            for grade in accuracy_grades:
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            summary['accuracy_analysis']['grade_distribution'] = grade_counts
            
            # Overall system grade
            avg_diff = summary['accuracy_analysis']['average_percentage_difference']
            if avg_diff <= 0.1:
                summary['overall_system_grade'] = "A+ (Excellent)"
            elif avg_diff <= 0.5:
                summary['overall_system_grade'] = "A (Very Good)"
            elif avg_diff <= 1.0:
                summary['overall_system_grade'] = "B (Good)"
            elif avg_diff <= 2.0:
                summary['overall_system_grade'] = "C (Fair)"
            else:
                summary['overall_system_grade'] = "D (Poor)"
        
        return summary

    def print_comprehensive_report(self, validation_results: Dict):
        """Print comprehensive validation report"""
        print("\n" + "="*90)
        print("📊 COMPREHENSIVE TRUEDATA VALIDATION REPORT")
        print("="*90)
        
        # Header
        start_time = datetime.fromisoformat(validation_results['start_time'])
        end_time = datetime.fromisoformat(validation_results['end_time']) if 'end_time' in validation_results else datetime.now()
        duration = end_time - start_time
        
        print(f"🕐 Test Duration: {duration.total_seconds():.1f} seconds")
        print(f"📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        # Summary metrics
        summary = validation_results.get('summary', {})
        
        print(f"\n📈 SYSTEM METRICS:")
        print(f"   Total Symbols Tested: {summary.get('total_symbols_tested', 0)}")
        print(f"   TrueData Available: {summary.get('truedata_symbols_available', 0)} ({summary.get('truedata_availability_rate', 0):.1f}%)")
        print(f"   Web Data Available: {summary.get('web_data_symbols_available', 0)} ({summary.get('web_data_availability_rate', 0):.1f}%)")
        print(f"   Successful Validations: {summary.get('completed_validations', 0)} ({summary.get('success_rate', 0):.1f}%)")
        
        # Accuracy metrics
        if 'accuracy_analysis' in summary:
            accuracy = summary['accuracy_analysis']
            print(f"\n🎯 ACCURACY ANALYSIS:")
            print(f"   Validated Symbols: {accuracy.get('total_accurate_validations', 0)}")
            print(f"   Average Difference: ±{accuracy.get('average_percentage_difference', 0):.3f}%")
            print(f"   Max Difference: ±{accuracy.get('max_percentage_difference', 0):.3f}%")
            print(f"   Min Difference: ±{accuracy.get('min_percentage_difference', 0):.3f}%")
            print(f"   Median Difference: ±{accuracy.get('median_percentage_difference', 0):.3f}%")
            
            if 'overall_system_grade' in summary:
                print(f"\n🏆 OVERALL SYSTEM GRADE: {summary['overall_system_grade']}")
            
            # Grade distribution
            if 'grade_distribution' in accuracy:
                print(f"\n📊 ACCURACY GRADE DISTRIBUTION:")
                for grade, count in accuracy['grade_distribution'].items():
                    print(f"   {grade}: {count} symbols")
        
        # Detailed results
        print(f"\n📋 DETAILED SYMBOL RESULTS:")
        results = validation_results.get('results', [])
        
        for result in results:
            symbol = result['symbol']
            status = result.get('status', 'unknown')
            
            if status == 'completed':
                truedata_price = result['truedata_data']['price']
                web_prices = result.get('web_prices', {})
                metrics = result.get('accuracy_metrics', {})
                
                grade = metrics.get('overall_grade', 'N/A')
                avg_diff = metrics.get('average_percentage_difference', 0)
                
                print(f"\n   ✅ {symbol}:")
                print(f"      TrueData: ₹{truedata_price:,.2f}")
                
                for source, price in web_prices.items():
                    comparison = metrics.get('comparisons', {}).get(source, {})
                    source_grade = comparison.get('accuracy_grade', 'N/A')
                    source_diff = comparison.get('percentage_difference', 0)
                    print(f"      {source}: ₹{price:,.2f} ({source_grade}, ±{source_diff:.3f}%)")
                
                print(f"      Overall: {grade} (±{avg_diff:.3f}%)")
                
            elif status == 'no_truedata':
                print(f"\n   ❌ {symbol}: No TrueData available")
            elif status == 'no_web_data':
                truedata_price = result.get('truedata_data', {}).get('price', 'N/A')
                print(f"\n   ⚠️  {symbol}: TrueData ₹{truedata_price} (No web data for comparison)")
            else:
                error = result.get('error', 'Unknown error')
                print(f"\n   ❌ {symbol}: {error}")
        
        # Final assessment
        print(f"\n" + "="*90)
        if validation_results.get('status') == 'completed':
            success_rate = summary.get('success_rate', 0)
            if 'overall_system_grade' in summary:
                system_grade = summary['overall_system_grade']
                print(f"🎉 VALIDATION COMPLETED: {system_grade} | Success Rate: {success_rate:.1f}%")
            else:
                print(f"✅ VALIDATION COMPLETED: Success Rate: {success_rate:.1f}%")
        else:
            print(f"❌ VALIDATION FAILED: {validation_results.get('error', 'Unknown error')}")
        print("="*90)

    def save_results(self, validation_results: Dict, filename: Optional[str] = None):
        """Save validation results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"systematic_truedata_validation_{timestamp}.json"
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Validation results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

async def main():
    """Main execution function"""
    validator = SimpleTrueDataValidator()
    
    try:
        # Run systematic validation
        print("🚀 Starting Systematic TrueData Validation...")
        results = await validator.run_systematic_validation()
        
        # Print comprehensive report
        validator.print_comprehensive_report(results)
        
        # Save results
        validator.save_results(results)
        
        # Return status for automation
        return results.get('status') == 'completed'
        
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Simple Systematic TrueData Validation Framework")
    print("⚡ Tests TrueData accuracy against web sources with comprehensive reporting")
    print("=" * 80)
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Validation completed successfully!")
        exit(0)
    else:
        print("\n❌ Validation failed!")
        exit(1) 