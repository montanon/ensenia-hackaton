#!/usr/bin/env python3
"""Database initialization script.

Run this script to create all database tables.
For development/hackathon use only.
"""

import asyncio
import logging

from app.ensenia.database.session import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialize database."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
