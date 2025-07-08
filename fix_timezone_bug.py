#!/usr/bin/env python3
"""Fix timezone bug in orchestrator.py"""

import re

# Read the orchestrator file
with open('src/core/orchestrator.py', 'r') as f:
    content = f.read()

# Add pytz import at the top
if 'import pytz' not in content:
    # Find the imports section and add pytz
    content = re.sub(
        r'(from datetime import datetime.*\n)', 
        r'\1import pytz\n', 
        content
    )

# Fix the _is_market_open method to use IST timezone
old_method = '''def _is_market_open(self) -> bool:
        """Check if market is open for trading"""
        try:
            from datetime import datetime, time
            now = datetime.now()
            
            # Indian market hours: 9:15 AM to 3:30 PM IST, Monday to Friday
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            market_start = time(9, 15)
            market_end = time(15, 30)
            current_time = now.time()
            
            return market_start <= current_time <= market_end
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False'''

new_method = '''def _is_market_open(self) -> bool:
        """Check if market is open for trading"""
        try:
            from datetime import datetime, time
            import pytz
            
            # Use IST timezone for accurate market hours
            ist_timezone = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist_timezone)
            
            # Indian market hours: 9:15 AM to 3:30 PM IST, Monday to Friday
            if now_ist.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            market_start = time(9, 15)
            market_end = time(15, 30)
            current_time = now_ist.time()
            
            return market_start <= current_time <= market_end
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False'''

# Replace the method
content = content.replace(old_method, new_method)

# Fix the RealSignal timestamp to use IST
old_timestamp = 'self.timestamp = datetime.now().isoformat()'
new_timestamp = '''import pytz
            ist_timezone = pytz.timezone('Asia/Kolkata')
            self.timestamp = datetime.now(ist_timezone).isoformat()'''

content = content.replace(old_timestamp, new_timestamp)

# Write back
with open('src/core/orchestrator.py', 'w') as f:
    f.write(content)

print('✅ Fixed timezone bug in orchestrator.py')
print('   - _is_market_open() now uses IST timezone')
print('   - RealSignal timestamps now use IST timezone')
print('   - Added pytz import') 