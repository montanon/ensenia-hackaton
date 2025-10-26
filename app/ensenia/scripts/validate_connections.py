"""Validate connections to R2, D1, Vectorize, and PostgreSQL.

This script tests connectivity and basic operations for all databases
used in the RAG pipeline.

Usage:
    python -m app.ensenia.scripts.validate_connections
"""

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


class ConnectionValidator:
    """Validates connections to all required services."""

    def __init__(self):
        """Initialize validator with service clients."""
        self.r2 = R2Service()
        self.d1 = D1Service()
        self.vectorize = VectorizeService()
        self.kv = KVService()
        self.validation_results = {
            "postgresql": {"connected": False, "error": None, "details": {}},
            "r2": {"connected": False, "error": None, "details": {}},
            "d1": {"connected": False, "error": None, "details": {}},
            "vectorize": {"connected": False, "error": None, "details": {}},
            "kv": {"connected": False, "error": None, "details": {}},
        }

    async def validate_postgresql(self) -> bool:
        """Validate PostgreSQL connection and check for required tables.

        Returns:
            True if connection successful, False otherwise

        """
        logger.info("=" * 60)
        logger.info("VALIDATING POSTGRESQL CONNECTION")
        logger.info("=" * 60)

        try:
            engine = create_async_engine(
                settings.database_url,
                echo=False,
                pool_pre_ping=True,
            )

            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

            async with async_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()

                msg = "✓ Connected to PostgreSQL"
                logger.info(msg)
                msg = f"  Version: {version[:50]}..."
                logger.info(msg)

                # Check for curriculum_content table
                check_table = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'curriculum_content'
                    )
                """)
                result = await session.execute(check_table)
                table_exists = result.scalar()

                if table_exists:
                    # Count records
                    count_query = text("SELECT COUNT(*) FROM curriculum_content")
                    result = await session.execute(count_query)
                    count = result.scalar()
                    msg = f"  Table curriculum_content: EXISTS ({count} records)"
                    logger.info(msg)
                    self.validation_results["postgresql"]["details"]["record_count"] = (
                        count
                    )
                else:
                    msg = "  Table curriculum_content: NOT FOUND"
                    logger.warning(msg)
                    msg = "  Run migrations to create tables"
                    logger.warning(msg)

                self.validation_results["postgresql"]["connected"] = True
                self.validation_results["postgresql"]["details"]["version"] = str(
                    version
                )[:50]
                self.validation_results["postgresql"]["details"]["table_exists"] = (
                    table_exists
                )

            await engine.dispose()
            return True

        except Exception:
            msg = "✗ PostgreSQL connection failed."
            logger.exception(msg)
            self.validation_results["postgresql"]["error"] = msg
            return False

    async def validate_r2(self) -> bool:
        """Validate R2 connection and bucket access.

        Returns:
            True if connection successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = "VALIDATING CLOUDFLARE R2 CONNECTION"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)

        try:
            # Test basic bucket access by listing objects
            objects = await self.r2.list_objects(prefix="", max_keys=1)

            msg = f"✓ Connected to R2 bucket: {settings.cloudflare_r2_bucket}"
            logger.info(msg)
            msg = f"  Endpoint: {settings.cloudflare_r2_endpoint}"
            logger.info(msg)

            # Get bucket info
            if "Contents" in objects:
                object_count = len(objects.get("Contents", []))
                msg = f"  Objects (sample): {object_count}"
                logger.info(msg)
            else:
                msg = "  Bucket is empty"
                logger.info(msg)

            self.validation_results["r2"]["connected"] = True
            self.validation_results["r2"]["details"]["bucket"] = (
                settings.cloudflare_r2_bucket
            )
            self.validation_results["r2"]["details"]["endpoint"] = (
                settings.cloudflare_r2_endpoint
            )

            return True

        except Exception:
            msg = "✗ R2 connection failed."
            logger.exception(msg)
            self.validation_results["r2"]["error"] = msg
            return False

    async def validate_d1(self) -> bool:
        """Validate D1 connection and table structure.

        Returns:
            True if connection successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = "VALIDATING CLOUDFLARE D1 CONNECTION"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)

        try:
            # Test basic query
            _ = await self.d1.query("SELECT 1 as test")

            msg = f"✓ Connected to D1 database: {settings.cloudflare_d1_database_id}"
            logger.info(msg)

            # Check for curriculum_content table
            table_check = await self.d1.query("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='curriculum_content'
            """)

            if table_check:
                # Count records
                count_result = await self.d1.query(
                    "SELECT COUNT(*) as count FROM curriculum_content"
                )
                count = count_result[0].get("count", 0) if count_result else 0
                msg = f"  Table curriculum_content: EXISTS ({count} records)"
                logger.info(msg)
                self.validation_results["d1"]["details"]["record_count"] = count
            else:
                logger.warning("  Table curriculum_content: NOT FOUND")
                logger.warning("  Run D1 schema setup to create tables")

            self.validation_results["d1"]["connected"] = True
            self.validation_results["d1"]["details"]["database_id"] = (
                settings.cloudflare_d1_database_id
            )

            return True

        except Exception:
            msg = "✗ D1 connection failed."
            logger.exception(msg)
            self.validation_results["d1"]["error"] = msg
            return False

    async def validate_vectorize(self) -> bool:
        """Validate Vectorize connection and index status.

        Returns:
            True if connection successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = "VALIDATING CLOUDFLARE VECTORIZE CONNECTION"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)

        try:
            # Get index info
            index_info = await self.vectorize.get_index_info()

            msg = (
                f"✓ Connected to Vectorize index: {settings.cloudflare_vectorize_index}"
            )
            logger.info(msg)
            msg = f"  Dimensions: {index_info.get('dimensions', 'N/A')}"
            logger.info(msg)
            msg = f"  Metric: {index_info.get('metric', 'N/A')}"
            logger.info(msg)

            # Try a simple query with a zero vector to check index health
            try:
                test_vector = [0.0] * settings.workers_ai_embedding_dimensions
                results = await self.vectorize.query(test_vector, top_k=1)
                vector_count = len(results)
                _msg = (
                    vector_count if vector_count > 0 else "Empty or unable to determine"
                )
                msg = f"  Vectors in index: {_msg}"
                logger.info(msg)
                self.validation_results["vectorize"]["details"]["vector_count"] = (
                    vector_count
                )
            except (ValueError, RuntimeError, OSError) as query_error:
                msg = f"  Could not query index: {query_error}"
                logger.warning(msg)
                self.validation_results["vectorize"]["details"]["vector_count"] = 0

            self.validation_results["vectorize"]["connected"] = True
            self.validation_results["vectorize"]["details"]["index_name"] = (
                settings.cloudflare_vectorize_index
            )
            self.validation_results["vectorize"]["details"]["dimensions"] = (
                index_info.get("dimensions")
            )

            return True

        except Exception as e:
            msg = f"✗ Vectorize connection failed: {e}"
            logger.exception(msg)
            self.validation_results["vectorize"]["error"] = str(e)
            return False

    async def validate_kv(self) -> bool:
        """Validate KV connection and namespace status.

        Returns:
            True if connection successful, False otherwise
        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = "VALIDATING CLOUDFLARE KV CONNECTION"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)

        try:
            # Get namespace info
            namespace_info = await self.kv.get_namespace_info()

            msg = f"✓ Connected to KV namespace: {settings.cloudflare_kv_namespace_id}"
            logger.info(msg)
            msg = f"  Title: {namespace_info.get('title', 'N/A')}"
            logger.info(msg)

            # List keys to check if namespace has data
            try:
                keys = await self.kv.list_keys(prefix="", limit=10)
                key_count = len(keys)
                msg = f"  Keys in namespace: {key_count if key_count > 0 else 'Empty or unable to determine'}"
                logger.info(msg)
                self.validation_results["kv"]["details"]["key_count"] = key_count
            except Exception as list_error:
                msg = f"  Could not list keys: {list_error}"
                logger.warning(msg)
                self.validation_results["kv"]["details"]["key_count"] = 0

            self.validation_results["kv"]["connected"] = True
            self.validation_results["kv"]["details"]["namespace_id"] = (
                settings.cloudflare_kv_namespace_id
            )
            self.validation_results["kv"]["details"]["title"] = namespace_info.get(
                "title"
            )

            return True

        except Exception as e:
            msg = f"✗ KV connection failed: {e}"
            logger.exception(msg)
            self.validation_results["kv"]["error"] = str(e)
            return False

    async def run_all_validations(self) -> bool:
        """Run all connection validations.

        Returns:
            True if all connections successful, False otherwise

        """
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = "RAG PIPELINE CONNECTION VALIDATION"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)

        results = {
            "postgresql": await self.validate_postgresql(),
            "r2": await self.validate_r2(),
            "d1": await self.validate_d1(),
            "vectorize": await self.validate_vectorize(),
            "kv": await self.validate_kv(),
        }

        # Summary
        msg = "\n" + "=" * 60
        logger.info(msg)
        msg = "VALIDATION SUMMARY"
        logger.info(msg)
        msg = "=" * 60
        logger.info(msg)

        all_connected = True
        for service, connected in results.items():
            status = "✓ CONNECTED" if connected else "✗ FAILED"
            msg = f"{service.upper():15} {status}"
            logger.info(msg)
            if not connected:
                all_connected = False
                error = self.validation_results[service].get("error")
                msg = f"               Error: {error}"
                logger.error(msg)

        logger.info("=" * 60)

        if all_connected:
            logger.info("\n✓ All connections validated successfully!")
            logger.info("You can now proceed with database population.")
        else:
            logger.error(
                "\n✗ Some connections failed. Please check your configuration."
            )
            logger.error("Review .env file and ensure all credentials are correct.")

        return all_connected

    def get_results(self) -> dict:
        """Get detailed validation results.

        Returns:
            Dictionary of validation results

        """
        return self.validation_results


async def main() -> None:
    """Entry point."""
    validator = ConnectionValidator()

    try:
        success = await validator.run_all_validations()
        sys.exit(0 if success else 1)

    except Exception:
        msg = "Validation failed with error."
        logger.exception(msg)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
