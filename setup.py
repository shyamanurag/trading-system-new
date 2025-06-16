from setuptools import setup, find_packages

setup(
    name="trading-system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0,<0.69.0",
        "uvicorn>=0.15.0,<0.16.0",
        "pydantic>=2.0.0,<3.0.0",
        "pydantic-settings>=2.0.0,<3.0.0",
        "sqlalchemy==1.4.50",
        "asyncpg>=0.27.0,<0.28.0",
        "redis>=4.5.0,<5.0.0",
        "python-dotenv>=0.19.0,<1.0.0",
        "psycopg2-binary==2.9.10",
        "gunicorn>=20.1.0,<21.0.0",
        "python-jose>=3.3.0,<4.0.0",
        "python-multipart==0.0.6",
        "PyJWT>=2.3.0,<3.0.0",
        "jinja2>=3.0.0,<4.0.0"
    ],
    python_requires=">=3.11",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated Trading System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-system",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
) 