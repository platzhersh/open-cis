"""FastAPI dependency injection utilities."""

from src.db.client import prisma
from src.ehrbase.client import ehrbase_client


async def get_prisma():
    """Get Prisma client instance."""
    return prisma


async def get_ehrbase():
    """Get EHRBase client instance."""
    return ehrbase_client
