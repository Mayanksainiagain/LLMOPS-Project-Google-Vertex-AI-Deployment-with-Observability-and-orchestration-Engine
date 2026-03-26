"""
Root conftest.py — Makes 'backend' importable for pytest.

Problem: When running `pytest backend/tests/`, Python doesn't know
that 'backend' is a package relative to this project root.

Solution: This file at the project root tells pytest to add
this directory to sys.path automatically.
"""
import sys
import os

# Add the project root to Python's module search path
sys.path.insert(0, os.path.dirname(__file__))
