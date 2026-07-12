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

from database.models import Assessment
from database.session import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Database reset complete")