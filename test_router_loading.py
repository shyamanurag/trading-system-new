"""
Quick test to check which routers are loading vs failing
"""
import sys
import traceback

# Add project root to path
sys.path.insert(0, '.')

# Test the router imports that are configured in main.py
router_imports = {
    'auth': ('src.api.auth', 'router_v1'),
    'market': ('src.api.market', 'router'),
    'users': ('src.api.users', 'router'),
    'trading_control': ('src.api.trading_control', 'router'),
    'truedata': ('src.api.truedata_integration', 'router'),
    'truedata_options': ('src.api.truedata_options', 'router'),
    'market_data': ('src.api.market_data', 'router'),
    'autonomous_trading': ('src.api.autonomous_trading', 'router'),
    'recommendations': ('src.api.recommendations', 'router'),
    'trade_management': ('src.api.trade_management', 'router'),
    'zerodha_auth': ('src.api.zerodha_auth', 'router'),
    'zerodha_daily_auth': ('src.api.zerodha_daily_auth', 'router'),
    'zerodha_multi_user': ('src.api.zerodha_multi_user_auth', 'router'),
    'websocket': ('src.api.websocket', 'router'),
    'monitoring': ('src.api.monitoring', 'router'),
    'webhooks': ('src.api.webhooks', 'router'),
    'order_management': ('src.api.order_management', 'router'),
    'position_management': ('src.api.position_management', 'router'),
    'strategy_management': ('src.api.strategy_management', 'router'),
    'risk_management': ('src.api.risk_management', 'router'),
    'performance': ('src.api.performance', 'router'),
    'error_monitoring': ('src.api.error_monitoring', 'router'),
    'database_health': ('src.api.database_health', 'router'),
    'dashboard': ('src.api.dashboard_api', 'router'),
    'reports': ('src.api.routes.reports', 'router'),
}

print("🔍 Testing Router Imports")
print("=" * 50)

loaded_routers = {}
failed_routers = {}

for router_name, (module_path, router_attr) in router_imports.items():
    try:
        module = __import__(module_path, fromlist=[router_attr])
        router = getattr(module, router_attr)
        loaded_routers[router_name] = True
        print(f"✅ {router_name}: SUCCESS")
    except Exception as e:
        failed_routers[router_name] = str(e)
        print(f"❌ {router_name}: {str(e)}")

print(f"\n📊 SUMMARY: {len(loaded_routers)}/{len(router_imports)} routers loaded successfully")

if failed_routers:
    print(f"\n🚨 FAILED ROUTERS ({len(failed_routers)}):")
    for name, error in failed_routers.items():
        print(f"   {name}: {error}")
        
    print(f"\n🔧 PRIORITY FIXES NEEDED:")
    priority_fixes = ['monitoring', 'order_management', 'position_management', 'trade_management']
    for router_name in priority_fixes:
        if router_name in failed_routers:
            print(f"   🎯 {router_name}: {failed_routers[router_name]}")

if loaded_routers:
    print(f"\n✅ WORKING ROUTERS ({len(loaded_routers)}):")
    for name in loaded_routers.keys():
        print(f"   ✓ {name}") 