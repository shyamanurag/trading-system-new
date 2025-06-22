"""
Backend routing fix for Digital Ocean deployment
Run this to update the API to handle path stripping correctly
"""

import os

# Update main.py to handle paths without leading slashes
def fix_main_py():
    """Add middleware to handle Digital Ocean path stripping"""
    
    middleware_code = """
# Middleware to fix Digital Ocean path stripping
@app.middleware("http")
async def fix_path_stripping(request: Request, call_next):
    # Log the original path
    original_path = request.url.path
    
    # If path doesn't start with /, add it
    if original_path and not original_path.startswith('/'):
        # Create a new URL with the leading slash
        from starlette.datastructures import URL
        new_url = URL(str(request.url).replace(original_path, f'/{original_path}', 1))
        request._url = new_url
        logger.info(f"Fixed path: {original_path} -> {new_url.path}")
    
    response = await call_next(request)
    return response
"""
    
    print("Add this middleware to main.py after the other middleware")
    print(middleware_code)

if __name__ == "__main__":
    fix_main_py()
