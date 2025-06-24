import time
import logging
from datetime import datetime

print('=== LOCAL TrueData Test ===')
print('Testing if TrueData works locally vs production')

local_data = {}
callback_count = 0

try:
    from truedata import TD_live
    print('TrueData library found')
    
    td_obj = TD_live('tdwsp697', 'shyam@697', live_port=8084, url='push.truedata.in', compression=False)
    print('TrueData connected')
    
    @td_obj.trade_callback
    def tick_callback(data):
        global local_data, callback_count
        callback_count += 1
        symbol = data.get('symbol', 'UNKNOWN')
        price = data.get('ltp', 0)
        local_data[symbol] = {'ltp': price, 'callback': callback_count}
        print(f'CALLBACK {callback_count}: {symbol} = Rs.{price}')
    
    print('Callbacks registered')
    
    result = td_obj.start_live_data(['NIFTY', 'BANKNIFTY'])
    print(f'start_live_data result: {result}')
    
    print('Waiting 30 seconds for data...')
    time.sleep(30)
    
    print(f'Final: {callback_count} callbacks, {len(local_data)} symbols')
    
    if callback_count > 0:
        print('SUCCESS: TrueData works locally!')
        print('ISSUE: DigitalOcean blocking TrueData')
    else:
        print('FAILURE: TrueData not working locally')
        print('ISSUE: Account or TrueData server problem')
    
except ImportError:
    print('TrueData library not installed')
    print('Run: pip install truedata')
except Exception as e:
    print(f'Error: {e}')

