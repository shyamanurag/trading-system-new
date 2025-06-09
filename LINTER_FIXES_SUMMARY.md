# Linter Fixes Summary

## Fixed Issues in websocket_manager.py

### 1. Optional Type Annotations
- Fixed `connection_id: str = None` → `connection_id: Optional[str] = None`
- Fixed `exclude_user: str = None` → `exclude_user: Optional[str] = None`
- Fixed return type `-> WebSocketManager` → `-> Optional[WebSocketManager]` for get_websocket_manager()

### 2. None Checks
- Added validation in `_handle_trading_event` to check if `user_id` is not None before using it
- This prevents passing None to functions expecting str

### 3. Type Safety Improvements
- All optional parameters now properly typed with Optional[T]
- Functions that can return None now have correct return type annotations

## Common Linter Issues to Watch For

1. **Optional Parameters**
   - Always use `Optional[Type]` when parameter can be None
   - Don't use `param: Type = None`

2. **Return Types**
   - If function can return None, use `Optional[Type]` or `Type | None`
   - Be explicit about what can be None

3. **None Checks**
   - Always validate optional values before using them
   - Use early returns or if statements to handle None cases

4. **Import Statements**
   - Ensure `Optional` is imported from `typing` when needed
   - Keep imports organized and remove unused ones

## Remaining Issues

Most linter issues have been resolved. The main types of issues that may remain:
- Unused imports (can be cleaned up)
- Line length warnings (style preference)
- Missing docstrings (documentation)

These are non-critical and don't affect functionality. 