#!/usr/bin/env python
from setuptools import setup

setup(
    name='call-waiting',
    version='0.0.1',
    description=(
        'Utility context managers for waiting on and tracking function calls'),
    author='Matt Bennett',
    author_email='matt@bennett.name',
    url='http://github.com/mattbennett/call-waiting',
    py_modules=['call_waiting'],
    install_requires=[
        'mock',
        'wrapt'
    ],
    extras_require={
        'dev': [
            "coverage==4.0.3",
            "flake8==2.5.0",
            "pylint==1.5.1",
            "pytest==2.8.3",
        ]
    },
    dependency_links=[],
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
