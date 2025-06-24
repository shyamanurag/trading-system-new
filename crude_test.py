try:
    from truedata import TD_live
    import time
    
    print('Testing TrueData CRUDE symbols...')
    
    td_obj = TD_live('tdwsp697', 'shyam@697', live_port=8084, url='push.truedata.in', compression=False)
    print('Connected successfully')
    
    symbols = ['CRUDEOIL2506165300CE', 'CRUDEOIL2506165300PE']
    print(f'Testing symbols: {symbols}')
    
    result = td_obj.start_live_data(symbols)
    print(f'start_live_data result: {result}')
    
    time.sleep(2)
    
    callback_fired = False
    
    @td_obj.trade_callback
    def my_tick_data(tick_data):
        global callback_fired
        callback_fired = True
        print('CALLBACK SUCCESS:', tick_data)
    
    print('Waiting 20 seconds for callbacks...')
    
    for i in range(4):
        time.sleep(5)
        print(f'Wait {(i+1)*5}s - Callback fired: {callback_fired}')
        if callback_fired:
            break
    
    if callback_fired:
        print('SUCCESS: Callbacks work with CRUDE symbols!')
        print('SOLUTION: Use proper NSE symbol format for your account')
    else:
        print('NO CALLBACKS: Either symbols unavailable or callback issue')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc() 