from setuptools import setup, find_packages

setup(
    name="trading-system",
    version="1.0.0",
    description="Advanced algorithmic trading system with regime adaptation and risk management",
    author="",
    author_email="",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if not line.startswith("#") and line.strip()
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "trading-system=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
) 