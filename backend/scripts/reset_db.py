"""
Database reset utility.

This module provides a script for resetting the application's database schema
during development. It drops all tables defined in the SQLAlchemy Base metadata
and recreates them according to the current ORM models.

WARNING:
    This operation permanently deletes all existing data in the database.
    Do not run this script in production environments.

Usage:
    cd /d/Work/Projects/ResillienceAI/backend
    python -m database.reset_db.py
"""

# Add backend to path
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.session import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Database reset complete")