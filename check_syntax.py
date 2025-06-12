import ast
import os
import glob
import traceback

def check_syntax_errors():
    """Check all Python files for syntax errors"""
    errors = []
    files_checked = 0
    
    # Get all Python files
    python_files = []
    for pattern in ['*.py', 'src/**/*.py', 'database/**/*.py', 'config/**/*.py']:
        python_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates
    python_files = list(set(python_files))
    
    print(f"Checking {len(python_files)} Python files for syntax errors...\n")
    
    for filepath in sorted(python_files):
        files_checked += 1
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content, filepath)
            
        except SyntaxError as e:
            errors.append({
                'file': filepath,
                'line': e.lineno,
                'offset': e.offset,
                'error': str(e.msg),
                'text': e.text
            })
        except Exception as e:
            errors.append({
                'file': filepath,
                'line': 0,
                'offset': 0,
                'error': f"Error reading file: {str(e)}",
                'text': None
            })
    
    # Report results
    if errors:
        print(f"Found {len(errors)} syntax errors:\n")
        for error in errors:
            print(f"File: {error['file']}")
            print(f"  Line {error['line']}, Column {error['offset']}: {error['error']}")
            if error['text']:
                print(f"  Code: {error['text'].strip()}")
            print()
    else:
        print(f"✅ No syntax errors found in {files_checked} files!")
    
    return errors

if __name__ == "__main__":
    check_syntax_errors() 