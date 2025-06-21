#!/usr/bin/env python3
"""Script to remove duplicate endpoints from main.py"""

def remove_duplicate_endpoints():
    """Remove duplicate endpoints without /api/ prefix"""
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start of the duplicate endpoints section
    start_marker = "# Add duplicate endpoints without /api/ prefix for frontend compatibility"
    end_marker = "if __name__ == \"__main__\":"
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos != -1 and end_pos != -1:
        # Remove the duplicate endpoints section
        new_content = content[:start_pos] + content[end_pos:]
        
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Duplicate endpoints removed successfully!")
    else:
        print("❌ Could not find duplicate endpoints section")

if __name__ == "__main__":
    remove_duplicate_endpoints() 