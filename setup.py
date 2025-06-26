from setuptools import setup, find_packages

setup(
    name="grox",
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
        "pyyaml>=6.0",
        "click>=8.0",
        "jinja2",
        "langfabric (>=0.1.6,<0.2.0)",
        "seyaml>=0.1.1,<1.0",
    ],
    entry_points={
        "console_scripts": ["grox = grox.cli:cli"]
    },
    package_data={
        "grox.templates": ["*.j2"]
    },
    python_requires=">=3.11,<4.0",
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
