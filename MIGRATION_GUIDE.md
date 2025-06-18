# Migration Guide: Python 3.13 to Python 3.11

## Why Migrate?

Python 3.13 has compatibility issues with:
- NumPy (core data processing)
- SQLAlchemy (database ORM)
- Many scientific packages
- Some trading libraries

## Migration Steps

### 1. Install Python 3.11
Follow the instructions in PYTHON311_SETUP_GUIDE.md

### 2. Backup Current Environment
```bash
pip freeze > requirements_backup.txt
```

### 3. Create New Virtual Environment
```bash
# Windows
python -m venv .venv311
.venv311\Scripts\activate

# Linux/macOS
python3.11 -m venv .venv311
source .venv311/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements_python311.txt
```

### 5. Test Installation
```bash
python test_imports.py
```

### 6. Update IDE/Editor
- VS Code: Select Python 3.11 interpreter
- PyCharm: Configure Python 3.11 interpreter
- Jupyter: Install ipykernel for Python 3.11

## Package Compatibility

### Fully Compatible (Python 3.11)
- FastAPI, Uvicorn
- Pandas, NumPy
- SQLAlchemy, Alembic
- Redis, Celery
- All trading libraries

### May Need Updates
- Some newer packages
- Development tools

## Troubleshooting

### Common Issues:
1. Import errors: Reinstall packages
2. Path issues: Update PATH environment variable
3. IDE issues: Reconfigure Python interpreter

### Commands:
```bash
# Check Python version
python --version

# Check pip version
pip --version

# List installed packages
pip list

# Test imports
python -c "import numpy, pandas, sqlalchemy; print('All good!')"
```

## Benefits After Migration

- Stable NumPy operations
- Reliable SQLAlchemy
- Better package compatibility
- Faster development
- Fewer runtime errors
