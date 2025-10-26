#!/usr/bin/env python3
"""Clean/wipe all RAG databases: PostgreSQL, D1, Vectorize, and R2.

This script provides options to:
1. Wipe all databases completely
2. Wipe specific databases selectively
3. Preview what would be deleted (dry-run mode)

⚠️  WARNING: This will permanently delete data! Use with caution.

Usage:
    # Dry-run (preview only)
    python -m app.ensenia.scripts.cleanup_databases --dry-run

    # Wipe all databases
    python -m app.ensenia.scripts.cleanup_databases --all

    # Wipe specific databases
    python -m app.ensenia.scripts.cleanup_databases --postgresql --vectorize

    # Force without confirmation
    python -m app.ensenia.scripts.cleanup_databases --all --force
"""

import argparse
import asyncio
import logging
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.ensenia.core.config import settings
from app.ensenia.services.cloudflare.d1 import D1Service
from app.ensenia.services.cloudflare.kv import KVService
from app.ensenia.services.cloudflare.r2 import R2Service
from app.ensenia.services.cloudflare.vectorize import VectorizeService

logger = logging.getLogger(__name__)

ITEM_BATCH_SIZE = 10000
NUM_OBJECTS_TO_SHOW = 5


class DatabaseCleaner:
    """Handles cleaning/wiping of all RAG databases."""

    def __init__(self, *, dry_run: bool = False) -> None:
        """Initialize cleaner.

        Args:
            dry_run: If True, only preview actions without executing

        """
        self.dry_run = dry_run
        self.r2 = R2Service()
        self.d1 = D1Service()
        self.vectorize = VectorizeService()
        self.kv = KVService()
        self.stats = {
            "postgresql": {"deleted": 0, "error": None},
            "d1": {"deleted": 0, "error": None},
            "vectorize": {"deleted": 0, "error": None},
            "r2": {"deleted": 0, "error": None},
            "kv": {"deleted": 0, "error": None},
        }

    async def clean_postgresql(self) -> bool:
        """Clean PostgreSQL curriculum_content table.

        Returns:
            True if successful, False otherwise

        """
        logger.info("=" * 60)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}CLEANING POSTGRESQL DATABASE"
        logger.info(msg)
        logger.info("=" * 60)

        try:
            engine = create_async_engine(settings.database_url, echo=False)
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

            async with async_session() as session:
                # Check if table exists
                check_table = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'curriculum_content'
                    )
                """)
                result = await session.execute(check_table)
                table_exists = result.scalar()

                if not table_exists:
                    logger.warning("Table curriculum_content does not exist, skipping")
                    return True

                # Count records
                count_query = text("SELECT COUNT(*) FROM curriculum_content")
                result = await session.execute(count_query)
                count = result.scalar()

                msg = f"Found {count} records in curriculum_content table"
                logger.info(msg)

                if count == 0:
                    logger.info("Table is already empty")
                    return True

                if not self.dry_run:
                    # Delete all records
                    delete_query = text("DELETE FROM curriculum_content")
                    await session.execute(delete_query)
                    await session.commit()
                    msg = f"✓ Deleted {count} records from curriculum_content"
                    logger.info(msg)
                    self.stats["postgresql"]["deleted"] = count
                else:
                    msg = f"[DRY RUN] Would delete {count} records"
                    logger.info(msg)

            await engine.dispose()
            return True

        except Exception:
            msg = "✗ PostgreSQL cleanup failed: {e}"
            logger.exception(msg)
            return False

    async def clean_d1(self) -> bool:
        """Clean D1 curriculum_content table.

        Returns:
            True if successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}CLEANING D1 DATABASE"
        logger.info(msg)
        logger.info("=" * 60)

        try:
            # Check if table exists
            table_check = await self.d1.query("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='curriculum_content'
            """)

            if not table_check:
                logger.warning("Table curriculum_content does not exist, skipping")
                return True

            # Count records
            count_result = await self.d1.query(
                "SELECT COUNT(*) as count FROM curriculum_content"
            )
            count = count_result[0].get("count", 0) if count_result else 0

            msg = f"Found {count} records in curriculum_content table"
            logger.info(msg)

            if count == 0:
                logger.info("Table is already empty")
                return True

            if not self.dry_run:
                # Delete all records
                await self.d1.execute("DELETE FROM curriculum_content")
                msg = f"✓ Deleted {count} records from curriculum_content"
                logger.info(msg)
                self.stats["d1"]["deleted"] = count
            else:
                msg = f"[DRY RUN] Would delete {count} records"
                logger.info(msg)

            return True

        except Exception:
            msg = "✗ D1 cleanup failed: {e}"
            logger.exception(msg)
            return False

    async def clean_vectorize(self) -> bool:
        """Clean Vectorize index by deleting all vectors.

        Returns:
            True if successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}CLEANING VECTORIZE INDEX"
        logger.info(msg)
        logger.info("=" * 60)

        try:
            # Get current vector count by querying with zero vector
            test_vector = [0.0] * settings.workers_ai_embedding_dimensions
            results = await self.vectorize.query(test_vector, top_k=100)

            vector_count = len(results)
            msg = f"Found approximately {vector_count} vectors in index"
            logger.info(msg)

            if vector_count == 0:
                logger.info("Index appears to be empty")
                return True

            if not self.dry_run:
                # Extract vector IDs and delete
                vector_ids = [result["id"] for result in results]

                if vector_ids:
                    await self.vectorize.delete_by_ids(vector_ids)
                    msg = f"✓ Deleted {len(vector_ids)} vectors from index"
                    logger.info(msg)
                    self.stats["vectorize"]["deleted"] = len(vector_ids)

                    # Note: This may not delete ALL vectors if there are more than 10000
                    if vector_count >= ITEM_BATCH_SIZE:
                        logger.warning(
                            "Index may contain more vectors. Run cleanup if needed."
                        )
            else:
                msg = f"[DRY RUN] Would delete approximately {vector_count} vectors"
                logger.info(msg)

            return True

        except Exception:
            msg = "✗ Vectorize cleanup failed: {e}"
            logger.exception(msg)
            return False

    async def clean_r2(self) -> bool:
        """Clean R2 bucket by deleting all curriculum-related objects.

        Returns:
            True if successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}CLEANING R2 BUCKET"
        logger.info(msg)
        logger.info("=" * 60)

        try:
            # List all objects
            contents = await self.r2.list_objects(prefix="", max_keys=1000)

            object_count = len(contents)

            msg = f"Found {object_count} objects in bucket"
            logger.info(msg)

            if object_count == 0:
                logger.info("Bucket is already empty")
                return True

            if not self.dry_run:
                # Delete each object
                deleted_count = 0
                for obj in contents:
                    key = obj["Key"]
                    await self.r2.delete_object(key)
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        msg = f"  Deleted {deleted_count}/{object_count} objects..."
                        logger.info(msg)

                msg = f"✓ Deleted {deleted_count} objects from R2 bucket"
                logger.info(msg)
                self.stats["r2"]["deleted"] = deleted_count

                # Note: If there are more than 1000 objects, run cleanup again
                if object_count >= ITEM_BATCH_SIZE / 10:
                    msg = (
                        "Bucket may contain more objects. Run cleanup again if needed."
                    )
                    logger.warning(msg)
            else:
                msg = f"[DRY RUN] Would delete {object_count} objects"
                logger.info(msg)
                for obj in contents[:5]:  # Show first 5
                    msg = f"  - {obj['Key']}"
                    logger.info(msg)
                if object_count > NUM_OBJECTS_TO_SHOW:
                    msg = f"  ... and {object_count - 5} more"
                    logger.info(msg)

            return True

        except Exception:
            msg = "✗ R2 cleanup failed: {e}"
            logger.exception(msg)
            return False

    async def clean_kv(self) -> bool:
        """Clean KV namespace by deleting all keys.

        Returns:
            True if successful, False otherwise
        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}CLEANING KV NAMESPACE"
        logger.info(msg)
        logger.info("=" * 60)

        try:
            # List all keys
            keys = await self.kv.list_keys(prefix="", limit=1000)

            key_count = len(keys)

            msg = f"Found {key_count} keys in namespace"
            logger.info(msg)

            if key_count == 0:
                logger.info("Namespace is already empty")
                return True

            if not self.dry_run:
                # Delete each key
                deleted_count = 0
                for key_info in keys:
                    key_name = key_info["name"]
                    # Remove the namespace prefix to get the actual key
                    if ":" in key_name:
                        actual_key = key_name.split(":", 1)[1]
                    else:
                        actual_key = key_name
                    await self.kv.delete(actual_key)
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        msg = f"  Deleted {deleted_count}/{key_count} keys..."
                        logger.info(msg)

                msg = f"✓ Deleted {deleted_count} keys from KV namespace"
                logger.info(msg)
                self.stats["kv"]["deleted"] = deleted_count

                # Note: If there are more than 1000 keys, run cleanup again
                if key_count >= 1000:
                    msg = (
                        "Namespace may contain more keys. Run cleanup again if needed."
                    )
                    logger.warning(msg)
            else:
                msg = f"[DRY RUN] Would delete {key_count} keys"
                logger.info(msg)
                for key_info in keys[:NUM_OBJECTS_TO_SHOW]:  # Show first 5
                    msg = f"  - {key_info['name']}"
                    logger.info(msg)
                if key_count > NUM_OBJECTS_TO_SHOW:
                    msg = f"  ... and {key_count - NUM_OBJECTS_TO_SHOW} more"
                    logger.info(msg)

            return True

        except Exception:
            msg = "✗ KV cleanup failed: {e}"
            logger.exception(msg)
            return False

    async def clean_all(
        self,
        *,
        clean_postgresql: bool = False,
        clean_d1: bool = False,
        clean_vectorize: bool = False,
        clean_r2: bool = False,
        clean_kv: bool = False,
    ) -> dict:
        """Clean selected databases.

        Args:
            clean_postgresql: Clean PostgreSQL database
            clean_d1: Clean D1 database
            clean_vectorize: Clean Vectorize index
            clean_r2: Clean R2 bucket

        Returns:
            Dictionary with cleanup results

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}DATABASE CLEANUP"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)
        msg = ""
        logger.info(msg)

        results = {}

        if clean_postgresql:
            results["postgresql"] = await self.clean_postgresql()

        if clean_d1:
            results["d1"] = await self.clean_d1()

        if clean_vectorize:
            results["vectorize"] = await self.clean_vectorize()

        if clean_r2:
            results["r2"] = await self.clean_r2()

        if clean_kv:
            results["kv"] = await self.clean_kv()

        # Summary
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = f"{'[DRY RUN] ' if self.dry_run else ''}CLEANUP SUMMARY"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)
        logger.info("=" * 60)

        for service, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            deleted = self.stats[service]["deleted"]
            msg = f"{service.upper():15} {status} ({deleted} items deleted)"
            logger.info(msg)

        logger.info("=" * 60)

        return results


async def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Clean/wipe RAG databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (preview only)
  python -m app.ensenia.scripts.cleanup_databases --dry-run

  # Clean all databases
  python -m app.ensenia.scripts.cleanup_databases --all

  # Clean specific databases
  python -m app.ensenia.scripts.cleanup_databases --postgresql --vectorize

⚠️  WARNING: This permanently deletes data! Always run --dry-run first.
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all databases (PostgreSQL, D1, Vectorize, R2, KV)",
    )
    parser.add_argument(
        "--postgresql", action="store_true", help="Clean PostgreSQL only"
    )
    parser.add_argument("--d1", action="store_true", help="Clean D1 only")
    parser.add_argument("--vectorize", action="store_true", help="Clean Vectorize only")
    parser.add_argument("--r2", action="store_true", help="Clean R2 only")
    parser.add_argument("--kv", action="store_true", help="Clean KV only")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    # Determine which databases to clean
    clean_pg = args.all or args.postgresql
    clean_d1_db = args.all or args.d1
    clean_vz = args.all or args.vectorize
    clean_r2_bucket = args.all or args.r2
    clean_kv_namespace = args.all or args.kv

    if not (clean_pg or clean_d1_db or clean_vz or clean_r2_bucket or clean_kv_namespace):
        parser.error("Specify at least one database to clean or use --all")

    # Confirmation prompt (unless force or dry-run)
    if not args.force and not args.dry_run:
        logger.warning("\n⚠️  WARNING: This will permanently delete data!")
        logger.warning("Databases to be cleaned:")
        if clean_pg:
            logger.warning("  - PostgreSQL curriculum_content table")
        if clean_d1_db:
            logger.warning("  - D1 curriculum_content table")
        if clean_vz:
            logger.warning("  - Vectorize index vectors")
        if clean_r2_bucket:
            logger.warning("  - R2 bucket objects")
        if clean_kv_namespace:
            logger.warning("  - KV namespace keys")

        response = input("\nAre you sure you want to proceed? Type 'yes' to confirm: ")
        if response.lower() != "yes":
            logger.info("Cleanup cancelled")
            sys.exit(0)

    cleaner = DatabaseCleaner(dry_run=args.dry_run)

    try:
        results = await cleaner.clean_all(
            clean_postgresql=clean_pg,
            clean_d1=clean_d1_db,
            clean_vectorize=clean_vz,
            clean_r2=clean_r2_bucket,
            clean_kv=clean_kv_namespace,
        )

        # Exit with error if any cleanup failed
        all_success = all(results.values())
        sys.exit(0 if all_success else 1)

    except Exception:
        msg = "Cleanup failed with error: {e}"
        logger.exception(msg)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
