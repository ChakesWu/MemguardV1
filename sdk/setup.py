"""
MemGuard SDK — Memory Observability for AI Agent Frameworks.

pip install -e .   # Install in development mode
"""

from setuptools import setup, find_packages

setup(
    name="memguard-sdk",
    version="0.1.0",
    description="Memory observability middleware for AI agent frameworks",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # No mandatory dependencies — transports use stdlib
        # Optional: install langgraph for the adapter
        # Optional: install aiohttp for async HTTP transport
    ],
    extras_require={
        "langgraph": ["langgraph>=0.2.0"],
        "dev": ["langgraph>=0.2.0", "pytest", "pytest-asyncio"],
    },
)
