import logging

from prisma import Json
from src.db.client import prisma

logger = logging.getLogger(__name__)


async def log_action(
    user_id: str,
    action: str,
    resource: str,
    resource_id: str | None = None,
    ehr_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Write an audit log entry for a mutating operation."""
    try:
        await prisma.auditlog.create(
            data={
                "userId": user_id,
                "action": action,
                "resource": resource,
                "resourceId": resource_id,
                "ehrId": ehr_id,
                "metadata": Json(metadata) if metadata is not None else None,
            }
        )
    except Exception:
        logger.exception("Failed to write audit log")
