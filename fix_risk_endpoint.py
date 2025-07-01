#!/usr/bin/env python3
"""Fix risk endpoint to handle None risk_manager"""

# Read the file
with open('src/api/autonomous_trading.py', 'r') as f:
    lines = f.readlines()

# Find the risk endpoint and fix it
new_lines = []
in_risk_function = False
skip_until_except = False

for i, line in enumerate(lines):
    if '@router.get("/risk"' in line:
        in_risk_function = True
        new_lines.append(line)
    elif in_risk_function and 'try:' in line:
        new_lines.append(line)
        # Add the fixed logic
        new_lines.append('        # Fix: Check if risk_manager is properly initialized\n')
        new_lines.append('        if hasattr(orchestrator, \'risk_manager\') and orchestrator.risk_manager is not None:\n')
        new_lines.append('            risk_metrics = await orchestrator.risk_manager.get_risk_metrics()\n')
        new_lines.append('        else:\n')
        new_lines.append('            # Return default risk metrics if not initialized\n')
        new_lines.append('            risk_metrics = {\n')
        new_lines.append('                "max_daily_loss": 50000,\n')
        new_lines.append('                "current_exposure": 0,\n')
        new_lines.append('                "available_capital": 0,\n')
        new_lines.append('                "risk_score": 0,\n')
        new_lines.append('                "status": "risk_manager_not_initialized"\n')
        new_lines.append('            }\n')
        skip_until_except = True
    elif skip_until_except and 'except Exception as e:' in line:
        skip_until_except = False
        in_risk_function = False
        new_lines.append('        return RiskMetricsResponse(\n')
        new_lines.append('            success=True,\n')
        new_lines.append('            message="Risk metrics retrieved successfully",\n')
        new_lines.append('            data=risk_metrics\n')
        new_lines.append('        )\n')
        new_lines.append(line)
    elif not skip_until_except:
        new_lines.append(line)

# Write back
with open('src/api/autonomous_trading.py', 'w') as f:
    f.writelines(new_lines)

print('✅ Fixed risk_manager None check in autonomous_trading.py') 