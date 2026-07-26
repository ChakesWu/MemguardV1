"""
MemGuard SDK — Memory Observability for AI Agent Frameworks.

pip install -e .   # Install in development mode
"""

from setuptools import setup, find_packages
import os

# Read README if it exists
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="memguard",
    version="0.1.0",
    description="Memory observability and security for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "langgraph": ["langgraph>=0.2.0"],
        "openai": ["openai>=1.0.0"],
        "rich": ["rich>=13.0.0"],
        "all": ["langgraph>=0.2.0", "openai>=1.0.0", "rich>=13.0.0"],
        "dev": ["pytest>=7.0.0", "pytest-asyncio>=0.21.0"],
    },
    author="MemGuard Team",
    keywords=["ai", "agents", "memory", "observability", "langgraph", "monitoring"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
