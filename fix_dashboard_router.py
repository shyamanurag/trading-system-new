"""
Fix Dashboard Router Mounting Issue
====================================

Issue: Dashboard endpoint returns 404 because of double prefix:
- Router mounted at: /api/v1/dashboard  
- Endpoint defined as: @router.get("/dashboard/summary")
- Final URL becomes: /api/v1/dashboard/dashboard/summary (wrong)
- Should be: /api/v1/dashboard/summary

Solution: Change router mounting to root ('') in main.py

Current main.py line 742:
    ('dashboard', '/api/v1/dashboard', ('dashboard',)),

Should be:
    ('dashboard', '', ('dashboard',)),

This works because the dashboard router already has full paths like:
- @router.get("/dashboard/summary") 
- @router.get("/performance/metrics")
- @router.get("/positions/current")
etc.
"""

# The fix is in main.py router_configs list:
FIX_MAIN_PY_LINE_742 = """
# Change this line:
('dashboard', '/api/v1/dashboard', ('dashboard',)),

# To this:
('dashboard', '', ('dashboard',)),
"""

print("Dashboard router mounting fix prepared.")
print("Change main.py line 742 as shown above.")
print("This will make /dashboard/summary available at the correct URL.") 