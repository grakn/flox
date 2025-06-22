from setuptools import setup, find_packages

setup(
    name="flox",
    version="0.1.0",
    description="Async-ready context and logging manager for multi-tenant services",
    author="Phragman",
    author_email="a@staphi.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=1.10.0,<3",
        "structlog>=23.1.0",
        "python-json-logger>=2.0.0",
        "pyyaml>=6.0"
    ],
    entry_points={
        "console_scripts": ["flox = flox.cli:cli"]
    },
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    extras_require={
        "test": [
            "pytest",
        ]
    },
)
