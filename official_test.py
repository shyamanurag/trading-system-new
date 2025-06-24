from truedata import TD_live
import time
import logging

print('=== OFFICIAL TrueData Pattern Test ===')

username = 'tdwsp697'
password = 'shyam@697'
port = 8086  # Official port from TrueData sample
url = 'push.truedata.in'

print(f'Connecting with official pattern: {username}@{url}:{port}')

td_obj = TD_live(username, password, live_port=port, log_level=logging.WARNING, url=url, compression=False)

# Use official symbols (options) from TrueData sample
symbols = ['CRUDEOIL2506165300CE', 'CRUDEOIL2506165300PE']
print(f'Using official symbols: {symbols}')

# CRITICAL: start_live_data FIRST (official pattern)
req_ids = td_obj.start_live_data(symbols)
print(f'start_live_data result: {req_ids}')
time.sleep(1)

# THEN register callbacks (official pattern)
@td_obj.trade_callback
def my_tick_data(tick_data):
    print('OFFICIAL TICK:', tick_data)

@td_obj.greek_callback
def mygreek_bidask(greek_data):
    print('OFFICIAL GREEK:', greek_data)

print('Official callbacks registered, waiting 30 seconds...')

# Wait for data
start_time = time.time()
while time.time() - start_time < 30:
    time.sleep(5)
    elapsed = int(time.time() - start_time)
    print(f'Waiting for official pattern data... ({elapsed}s)')

print('OFFICIAL PATTERN TEST COMPLETE') 