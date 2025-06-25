#!/usr/bin/env python3
"""
Systematic TrueData Validation Framework
Tests TrueData accuracy against multiple web sources with comprehensive reporting
"""

import asyncio
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path
import statistics
import re

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

class WebPriceSource:
    """Web price source configuration"""
    def __init__(self, name: str, url_template: str, price_extractor: callable):
        self.name = name
        self.url_template = url_template
        self.price_extractor = price_extractor

class SystematicTrueDataValidator:
    def __init__(self):
        self.td_client = None
        self.test_symbols = [
            "RELIANCE",
            "TCS", 
            "INFY",
            "HDFC",
            "ICICIBANK",
            "SBIN",
            "ITC",
            "HDFCBANK",
            "BHARTIARTL",
            "KOTAKBANK"
        ]
        
        # Real subscription credentials
        self.username = "tdwsp697"
        self.password = "shyam@697"
        self.port = 8084
        
        # Web sources for price verification
        self.web_sources = [
            WebPriceSource(
                "Yahoo Finance",
                "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS",
                self._extract_yahoo_price
            ),
            WebPriceSource(
                "NSE Official",
                "https://www.nseindia.com/api/quote-equity?symbol={symbol}",
                self._extract_nse_price
            )
        ]
        
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _extract_yahoo_price(self, response_data: dict, symbol: str) -> Optional[float]:
        """Extract price from Yahoo Finance API response"""
        try:
            if 'chart' in response_data and 'result' in response_data['chart']:
                result = response_data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return float(result['meta']['regularMarketPrice'])
        except:
            pass
        return None

    def _extract_nse_price(self, response_data: dict, symbol: str) -> Optional[float]:
        """Extract price from NSE API response"""
        try:
            if 'priceInfo' in response_data and 'lastPrice' in response_data['priceInfo']:
                return float(response_data['priceInfo']['lastPrice'])
        except:
            pass
        return None

    async def get_web_price(self, symbol: str, source: WebPriceSource) -> Optional[float]:
        """Get price from web source"""
        try:
            url = source.url_template.format(symbol=symbol)
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return source.price_extractor(data, symbol)
        except Exception as e:
            print(f"❌ Error fetching {symbol} from {source.name}: {e}")
        return None

    async def get_all_web_prices(self, symbol: str) -> Dict[str, float]:
        """Get prices from all web sources"""
        web_prices = {}
        
        for source in self.web_sources:
            price = await self.get_web_price(symbol, source)
            if price:
                web_prices[source.name] = price
                
        return web_prices

    def connect_truedata(self) -> bool:
        """Connect to TrueData"""
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
                return True
            else:
                print("❌ TrueData connection failed")
                return False
                
        except Exception as e:
            print(f"❌ TrueData connection error: {e}")
            return False

    def get_truedata_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get prices from TrueData for multiple symbols"""
        if not self.td_client:
            return {}
            
        try:
            print(f"📊 Requesting data for {len(symbols)} symbols from TrueData...")
            
            # Subscribe to symbols
            for symbol in symbols:
                try:
                    self.td_client.live_data_request([symbol])
                    time.sleep(0.1)  # Small delay between requests
                except Exception as e:
                    print(f"❌ Error subscribing to {symbol}: {e}")
            
            # Wait for data to populate
            time.sleep(3)
            
            # Get live data
            raw_data = self.td_client.get_live_data()
            print(f"📦 Raw TrueData response: {raw_data}")
            
            # Parse TrueData response
            parsed_data = {}
            if raw_data and isinstance(raw_data, list):
                for item in raw_data:
                    if isinstance(item, list) and len(item) >= 6:
                        symbol = item[0]
                        timestamp = item[2] if len(item) > 2 else None
                        ltp = float(item[5]) if len(item) > 5 and item[5] else None
                        volume = int(item[6]) if len(item) > 6 and item[6] else None
                        high = float(item[7]) if len(item) > 7 and item[7] else None
                        low = float(item[8]) if len(item) > 8 and item[8] else None
                        
                        if ltp:
                            parsed_data[symbol] = {
                                'price': ltp,
                                'timestamp': timestamp,
                                'volume': volume,
                                'high': high,
                                'low': low,
                                'raw_data': item
                            }
                            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error getting TrueData prices: {e}")
            return {}

    def calculate_accuracy_metrics(self, truedata_price: float, web_prices: Dict[str, float]) -> Dict:
        """Calculate accuracy metrics"""
        if not web_prices:
            return {'status': 'no_web_data'}
            
        # Calculate differences
        differences = []
        percentage_differences = []
        comparisons = {}
        
        for source, web_price in web_prices.items():
            diff = abs(truedata_price - web_price)
            pct_diff = (diff / web_price) * 100 if web_price > 0 else 0
            
            differences.append(diff)
            percentage_differences.append(pct_diff)
            
            comparisons[source] = {
                'web_price': web_price,
                'difference': diff,
                'percentage_difference': pct_diff,
                'accuracy_grade': self._get_accuracy_grade(pct_diff)
            }
        
        # Overall metrics
        avg_pct_diff = statistics.mean(percentage_differences)
        max_pct_diff = max(percentage_differences)
        min_pct_diff = min(percentage_differences)
        
        return {
            'status': 'success',
            'average_percentage_difference': avg_pct_diff,
            'max_percentage_difference': max_pct_diff,
            'min_percentage_difference': min_pct_diff,
            'overall_accuracy_grade': self._get_accuracy_grade(avg_pct_diff),
            'comparisons': comparisons,
            'web_price_range': {
                'min': min(web_prices.values()),
                'max': max(web_prices.values()),
                'avg': statistics.mean(web_prices.values())
            }
        }

    def _get_accuracy_grade(self, percentage_diff: float) -> str:
        """Get accuracy grade based on percentage difference"""
        if percentage_diff <= 0.1:
            return "A+ (Excellent)"
        elif percentage_diff <= 0.5:
            return "A (Very Good)"
        elif percentage_diff <= 1.0:
            return "B (Good)"
        elif percentage_diff <= 2.0:
            return "C (Fair)"
        else:
            return "D (Poor)"

    async def validate_symbol(self, symbol: str, truedata_data: Dict) -> Dict:
        """Validate a single symbol"""
        print(f"\n🔍 Validating {symbol}...")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'truedata_available': symbol in truedata_data,
            'status': 'pending'
        }
        
        if symbol not in truedata_data:
            result['status'] = 'no_truedata'
            result['error'] = 'Symbol not found in TrueData response'
            return result
            
        truedata_info = truedata_data[symbol]
        truedata_price = truedata_info['price']
        
        result['truedata_data'] = truedata_info
        
        # Get web prices
        print(f"   📡 Fetching web prices for {symbol}...")
        web_prices = await self.get_all_web_prices(symbol)
        
        result['web_prices'] = web_prices
        
        if not web_prices:
            result['status'] = 'no_web_data'
            result['warning'] = 'No web prices available for comparison'
            return result
            
        # Calculate accuracy metrics
        metrics = self.calculate_accuracy_metrics(truedata_price, web_prices)
        result['accuracy_metrics'] = metrics
        result['status'] = 'completed'
        
        # Print summary
        print(f"   💰 TrueData Price: ₹{truedata_price:,.2f}")
        for source, price in web_prices.items():
            print(f"   🌐 {source}: ₹{price:,.2f}")
        print(f"   📊 Accuracy Grade: {metrics.get('overall_accuracy_grade', 'N/A')}")
        print(f"   📈 Avg Difference: {metrics.get('average_percentage_difference', 0):.3f}%")
        
        return result

    async def run_systematic_validation(self) -> Dict:
        """Run systematic validation for all symbols"""
        print("🚀 Starting Systematic TrueData Validation")
        print("="*60)
        
        validation_results = {
            'start_time': datetime.now().isoformat(),
            'symbols_tested': self.test_symbols,
            'results': [],
            'summary': {}
        }
        
        # Connect to TrueData
        if not self.connect_truedata():
            validation_results['status'] = 'failed'
            validation_results['error'] = 'TrueData connection failed'
            return validation_results
            
        # Get TrueData prices for all symbols
        print(f"\n📊 Testing {len(self.test_symbols)} symbols...")
        truedata_data = self.get_truedata_prices(self.test_symbols)
        
        if not truedata_data:
            validation_results['status'] = 'failed'
            validation_results['error'] = 'No TrueData data received'
            return validation_results
            
        print(f"✅ Received TrueData for {len(truedata_data)} symbols")
        
        # Validate each symbol
        for symbol in self.test_symbols:
            try:
                result = await self.validate_symbol(symbol, truedata_data)
                validation_results['results'].append(result)
                
                # Small delay between validations
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error validating {symbol}: {e}")
                validation_results['results'].append({
                    'symbol': symbol,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Generate summary
        validation_results['summary'] = self._generate_summary(validation_results['results'])
        validation_results['end_time'] = datetime.now().isoformat()
        validation_results['status'] = 'completed'
        
        return validation_results

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate validation summary"""
        total_symbols = len(results)
        successful_validations = len([r for r in results if r.get('status') == 'completed'])
        truedata_available = len([r for r in results if r.get('truedata_available', False)])
        
        accuracy_grades = []
        avg_differences = []
        
        for result in results:
            if result.get('status') == 'completed' and 'accuracy_metrics' in result:
                metrics = result['accuracy_metrics']
                if 'average_percentage_difference' in metrics:
                    avg_differences.append(metrics['average_percentage_difference'])
                    grade = metrics.get('overall_accuracy_grade', '')
                    accuracy_grades.append(grade)
        
        summary = {
            'total_symbols_tested': total_symbols,
            'successful_validations': successful_validations,
            'truedata_symbols_available': truedata_available,
            'success_rate': (successful_validations / total_symbols * 100) if total_symbols > 0 else 0,
            'truedata_availability_rate': (truedata_available / total_symbols * 100) if total_symbols > 0 else 0
        }
        
        if avg_differences:
            summary['overall_accuracy'] = {
                'average_percentage_difference': statistics.mean(avg_differences),
                'max_percentage_difference': max(avg_differences),
                'min_percentage_difference': min(avg_differences),
                'accuracy_distribution': {grade: accuracy_grades.count(grade) for grade in set(accuracy_grades)}
            }
        
        return summary

    def print_detailed_report(self, validation_results: Dict):
        """Print detailed validation report"""
        print("\n" + "="*80)
        print("📊 SYSTEMATIC TRUEDATA VALIDATION REPORT")
        print("="*80)
        
        # Header info
        start_time = datetime.fromisoformat(validation_results['start_time'])
        end_time = datetime.fromisoformat(validation_results['end_time']) if 'end_time' in validation_results else datetime.now()
        duration = end_time - start_time
        
        print(f"🕐 Test Duration: {duration.total_seconds():.1f} seconds")
        print(f"📅 Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        # Summary
        summary = validation_results.get('summary', {})
        print(f"\n📈 SUMMARY METRICS:")
        print(f"   Total Symbols: {summary.get('total_symbols_tested', 0)}")
        print(f"   Successful Validations: {summary.get('successful_validations', 0)}")
        print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   TrueData Availability: {summary.get('truedata_availability_rate', 0):.1f}%")
        
        if 'overall_accuracy' in summary:
            accuracy = summary['overall_accuracy']
            print(f"\n🎯 ACCURACY METRICS:")
            print(f"   Average Difference: {accuracy.get('average_percentage_difference', 0):.3f}%")
            print(f"   Max Difference: {accuracy.get('max_percentage_difference', 0):.3f}%")
            print(f"   Min Difference: {accuracy.get('min_percentage_difference', 0):.3f}%")
            
            print(f"\n🏆 ACCURACY GRADES:")
            for grade, count in accuracy.get('accuracy_distribution', {}).items():
                print(f"   {grade}: {count} symbols")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in validation_results.get('results', []):
            symbol = result['symbol']
            status = result.get('status', 'unknown')
            
            if status == 'completed':
                truedata_price = result['truedata_data']['price']
                web_prices = result.get('web_prices', {})
                metrics = result.get('accuracy_metrics', {})
                grade = metrics.get('overall_accuracy_grade', 'N/A')
                avg_diff = metrics.get('average_percentage_difference', 0)
                
                print(f"\n   ✅ {symbol}:")
                print(f"      TrueData: ₹{truedata_price:,.2f}")
                for source, price in web_prices.items():
                    print(f"      {source}: ₹{price:,.2f}")
                print(f"      Grade: {grade} (±{avg_diff:.3f}%)")
                
            elif status == 'no_truedata':
                print(f"\n   ❌ {symbol}: No TrueData available")
            elif status == 'no_web_data':
                truedata_price = result['truedata_data']['price']
                print(f"\n   ⚠️  {symbol}: TrueData ₹{truedata_price:,.2f} (No web data for comparison)")
            else:
                print(f"\n   ❌ {symbol}: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*80)

    def save_results(self, validation_results: Dict, filename: Optional[str] = None):
        """Save validation results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"truedata_validation_{timestamp}.json"
            
        with open(filename, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
            
        print(f"💾 Results saved to: {filename}")

async def main():
    """Main function"""
    validator = SystematicTrueDataValidator()
    
    try:
        # Run systematic validation
        results = await validator.run_systematic_validation()
        
        # Print detailed report
        validator.print_detailed_report(results)
        
        # Save results
        validator.save_results(results)
        
        # Print final status
        if results.get('status') == 'completed':
            summary = results.get('summary', {})
            success_rate = summary.get('success_rate', 0)
            
            if success_rate >= 80:
                print(f"\n🎉 VALIDATION PASSED! Success Rate: {success_rate:.1f}%")
            else:
                print(f"\n⚠️  VALIDATION CONCERNS! Success Rate: {success_rate:.1f}%")
        else:
            print(f"\n❌ VALIDATION FAILED!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")

if __name__ == "__main__":
    print("🚀 Systematic TrueData Validation Framework")
    print("🔍 Testing TrueData accuracy against multiple web sources")
    asyncio.run(main()) 