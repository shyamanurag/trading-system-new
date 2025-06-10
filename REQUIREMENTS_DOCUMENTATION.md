# Requirements Files Documentation

This project uses multiple requirements files for different deployment scenarios:

## requirements.txt
**Purpose**: Main requirements file for local development and standard deployments
- Includes ALL dependencies including ML/AI libraries
- Used for development environments where full functionality is needed
- Contains gunicorn for production WSGI server
- Includes optional deep learning packages (commented out by default)

## docker-requirements.txt
**Purpose**: Optimized requirements for Docker container builds
- Excludes heavy ML/AI libraries to reduce image size
- Excludes gunicorn (handled by Docker CMD/ENTRYPOINT)
- Focuses on core trading system functionality
- Results in smaller, faster-building Docker images

## requirements-test.txt
**Purpose**: Testing and development tools
- Contains testing frameworks (pytest, pytest-asyncio)
- Code quality tools (black, flake8, mypy)
- Security scanning (bandit, safety)
- Not needed in production deployments

## When to use each file:

### Local Development:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For running tests
```

### Docker Builds:
```dockerfile
COPY docker-requirements.txt requirements.txt
RUN pip install -r requirements.txt
```

### CI/CD Testing:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Production (non-Docker):
```bash
pip install -r requirements.txt
```

## Key Differences:

| Package Type | requirements.txt | docker-requirements.txt | requirements-test.txt |
|--------------|------------------|------------------------|----------------------|
| Core API | ✓ | ✓ | ✗ |
| Database | ✓ | ✓ | ✗ |
| ML/AI Libraries | ✓ | ✗ | ✗ |
| Testing Tools | ✗ | ✗ | ✓ |
| Gunicorn | ✓ | ✗ | ✗ |
| Development Tools | ✗ | ✗ | ✓ | 