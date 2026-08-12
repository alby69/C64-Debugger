from setuptools import setup, find_packages

setup(
    name="c64debugger",
    version="0.5.0",
    packages=find_packages(),
    install_requires=[],
    author="Alberto Abate",
    description="C64 debugging, step execution and simulation tools",
    entry_points={
        "console_scripts": [
            "c64debugger = c64debugger.cli.main:main",
        ]
    }
)
