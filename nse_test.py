try:
    from truedata import TD_live
    import time
    
    print('Testing TrueData NSE symbols (your account subscription)...')
    
    td_obj = TD_live('tdwsp697', 'shyam@697', live_port=8084, url='push.truedata.in', compression=False)
    print('Connected successfully')
    
    # Test NSE symbols your account supports: NSE Equity, NSE F&O, Indices
    symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFC']
    print(f'Testing NSE symbols: {symbols}')
    
    result = td_obj.start_live_data(symbols)
    print(f'start_live_data result: {result}')
    
    time.sleep(2)
    
    callback_fired = False
    callback_count = 0
    
    @td_obj.trade_callback
    def my_tick_data(tick_data):
        global callback_fired, callback_count
        callback_fired = True
        callback_count += 1
        symbol = tick_data.get('symbol', 'UNKNOWN')
        ltp = tick_data.get('ltp', 0)
        print(f'NSE CALLBACK #{callback_count}: {symbol} = Rs.{ltp}')
    
    print('Waiting 30 seconds for NSE callbacks...')
    
    for i in range(6):
        time.sleep(5)
        print(f'Wait {(i+1)*5}s - Callbacks: {callback_count}')
        if callback_fired:
            print(f'SUCCESS: TrueData callbacks work with NSE symbols!')
            break
    
    if callback_fired:
        print(f'\nFINAL SUCCESS: {callback_count} callbacks received')
        print('SOLUTION: Update production to use NSE symbols')
        print('ISSUE WAS: Using CRUDE (commodity) instead of NSE symbols')
    else:
        print('\nSTILL NO CALLBACKS: May need different NSE symbol format')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc() 