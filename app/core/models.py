"""
Base models and mixins for common database functionality.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

class TimestampMixin:
    """Add timestamp fields to models."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UUIDMixin:
    """Add UUID field to models."""
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)

# Additional base model mixins can be added here as needed
# For example:
# class SoftDeleteMixin:
#     """Add soft delete functionality to models."""
#     deleted_at = Column(DateTime(timezone=True), nullable=True)
#     is_deleted = Column(Boolean, default=False)
#
#     def soft_delete(self):
#         self.deleted_at = datetime.now(timezone.utc)
#         self.is_deleted = True
