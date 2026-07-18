"""
Unit tests for CHAETRA's database models.
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    BaseModel,
    TimeStampedMixin,
    SoftDeleteMixin,
    UUIDMixin,
    AuditMixin,
    VersionMixin
)
from app.core.database import Base
from app.core.config import get_settings

settings = get_settings()

# Test model implementations
class TestModel(BaseModel):
    """Test model with all mixins"""
    __tablename__ = "test_models"
    name = Column(String(100))
    value = Column(Float)

class SimpleModel(Base, TimeStampedMixin):
    """Simple model with only timestamps"""
    __tablename__ = "simple_models"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

@pytest.mark.asyncio
async def test_timestamps(db_session: AsyncSession):
    """Test TimeStampedMixin functionality"""
    # Create model instance
    model = SimpleModel(name="test")
    db_session.add(model)
    await db_session.commit()
    
    # Verify timestamps
    assert model.created_at is not None
    assert model.updated_at is not None
    assert model.created_at <= model.updated_at
    
    # Update model
    original_updated_at = model.updated_at
    model.name = "updated"
    await db_session.commit()
    
    # Verify updated_at changed
    assert model.updated_at > original_updated_at
    # Verify created_at didn't change
    assert model.created_at < model.updated_at

@pytest.mark.asyncio
async def test_soft_delete(db_session: AsyncSession):
    """Test SoftDeleteMixin functionality"""
    model = TestModel(name="test")
    db_session.add(model)
    await db_session.commit()
    
    # Test soft delete
    model.soft_delete()
    await db_session.commit()
    
    assert model.is_deleted
    assert model.deleted_at is not None
    
    # Test restore
    model.restore()
    await db_session.commit()
    
    assert not model.is_deleted
    assert model.deleted_at is None

def test_uuid_generation():
    """Test UUIDMixin functionality"""
    model = TestModel(name="test")
    
    assert model.id is not None
    assert len(model.id) == 36  # UUID string length
    
    # Test custom UUID
    custom_uuid = "12345678-1234-5678-1234-567812345678"
    model_with_uuid = TestModel(id=custom_uuid, name="test")
    assert model_with_uuid.id == custom_uuid

@pytest.mark.asyncio
async def test_audit_fields(db_session: AsyncSession):
    """Test AuditMixin functionality"""
    model = TestModel(name="test")
    
    # Set audit fields
    test_user_id = "test-user-123"
    model.set_created_by(test_user_id)
    model.set_updated_by(test_user_id)
    
    db_session.add(model)
    await db_session.commit()
    
    assert model.created_by == test_user_id
    assert model.updated_by == test_user_id
    
    # Update with different user
    new_user_id = "new-user-456"
    model.set_updated_by(new_user_id)
    await db_session.commit()
    
    assert model.created_by == test_user_id  # Shouldn't change
    assert model.updated_by == new_user_id

@pytest.mark.asyncio
async def test_version_control(db_session: AsyncSession):
    """Test VersionMixin functionality"""
    model = TestModel(name="test")
    db_session.add(model)
    await db_session.commit()
    
    assert model.version == 1
    
    # Update version
    model.increment_version()
    await db_session.commit()
    
    assert model.version == 2

@pytest.mark.asyncio
async def test_base_model_methods(db_session: AsyncSession):
    """Test BaseModel utility methods"""
    # Test to_dict
    test_data = {
        "name": "test",
        "value": 42.0
    }
    model = TestModel(**test_data)
    db_session.add(model)
    await db_session.commit()
    
    model_dict = model.to_dict()
    assert model_dict["name"] == test_data["name"]
    assert model_dict["value"] == test_data["value"]
    assert "id" in model_dict
    assert "created_at" in model_dict
    assert "updated_at" in model_dict
    
    # Test from_dict
    new_data = {
        "name": "updated",
        "value": 99.9
    }
    new_model = TestModel.from_dict(new_data)
    assert new_model.name == new_data["name"]
    assert new_model.value == new_data["value"]
    
    # Test update
    update_data = {"name": "modified"}
    model.update(update_data)
    assert model.name == "modified"
    assert model.value == test_data["value"]  # Unchanged

@pytest.mark.asyncio
async def test_model_timestamps_auto_update(db_session: AsyncSession):
    """Test automatic timestamp updates"""
    model = TestModel(name="test")
    db_session.add(model)
    await db_session.commit()
    
    initial_updated_at = model.updated_at
    await db_session.refresh(model)
    
    # Wait a moment to ensure timestamp difference
    await asyncio.sleep(0.1)
    
    # Update model
    model.name = "updated"
    await db_session.commit()
    await db_session.refresh(model)
    
    assert model.updated_at > initial_updated_at

@pytest.mark.asyncio
async def test_model_relationships(db_session: AsyncSession):
    """Test model with relationships"""
    
    class ParentModel(BaseModel):
        """Parent model for relationship testing"""
        __tablename__ = "parent_models"
        name = Column(String(100))
    
    class ChildModel(BaseModel):
        """Child model for relationship testing"""
        __tablename__ = "child_models"
        name = Column(String(100))
        parent_id = Column(String(36), ForeignKey("parent_models.id"))
        parent = relationship(ParentModel, backref="children")
    
    # Create parent and child
    parent = ParentModel(name="parent")
    child = ChildModel(name="child")
    child.parent = parent
    
    db_session.add(parent)
    db_session.add(child)
    await db_session.commit()
    
    # Test relationships
    assert child.parent_id == parent.id
    assert child in parent.children

@pytest.mark.asyncio
async def test_model_validation(db_session: AsyncSession):
    """Test model validation logic"""
    
    class ValidatedModel(BaseModel):
        """Model with validation"""
        __tablename__ = "validated_models"
        name = Column(String(100))
        age = Column(Integer)
        
        def validate(self) -> bool:
            """Validate model data"""
            return len(self.name) > 0 and self.age >= 0
    
    # Valid model
    valid_model = ValidatedModel(name="test", age=25)
    assert valid_model.validate()
    
    # Invalid model
    invalid_model = ValidatedModel(name="", age=-1)
    assert not invalid_model.validate()

@pytest.mark.asyncio
async def test_model_inheritance(db_session: AsyncSession):
    """Test model inheritance"""
    
    class BaseProduct(BaseModel):
        """Base product model"""
        __tablename__ = "base_products"
        name = Column(String(100))
        price = Column(Float)
        
        __mapper_args__ = {
            "polymorphic_on": Column("type", String(50)),
            "polymorphic_identity": "base"
        }
    
    class DigitalProduct(BaseProduct):
        """Digital product model"""
        __tablename__ = "digital_products"
        id = Column(String(36), ForeignKey("base_products.id"), primary_key=True)
        download_url = Column(String(200))
        
        __mapper_args__ = {
            "polymorphic_identity": "digital"
        }
    
    class PhysicalProduct(BaseProduct):
        """Physical product model"""
        __tablename__ = "physical_products"
        id = Column(String(36), ForeignKey("base_products.id"), primary_key=True)
        weight = Column(Float)
        
        __mapper_args__ = {
            "polymorphic_identity": "physical"
        }
    
    # Create products
    digital = DigitalProduct(
        name="Software",
        price=99.99,
        download_url="https://example.com/download"
    )
    physical = PhysicalProduct(
        name="Book",
        price=29.99,
        weight=1.5
    )
    
    db_session.add_all([digital, physical])
    await db_session.commit()
    
    # Test inheritance
    assert isinstance(digital, BaseProduct)
    assert isinstance(physical, BaseProduct)
    assert hasattr(digital, "download_url")
    assert hasattr(physical, "weight")

@pytest.mark.asyncio
async def test_model_hooks(db_session: AsyncSession):
    """Test model lifecycle hooks"""
    
    class HookedModel(BaseModel):
        """Model with hooks"""
        __tablename__ = "hooked_models"
        name = Column(String(100))
        processed = Column(Boolean, default=False)
        
        def before_save(self):
            """Pre-save hook"""
            self.name = self.name.strip().title()
        
        def after_save(self):
            """Post-save hook"""
            self.processed = True
    
    # Create model
    model = HookedModel(name=" test model ")
    model.before_save()
    db_session.add(model)
    await db_session.commit()
    model.after_save()
    
    assert model.name == "Test Model"
    assert model.processed

if __name__ == "__main__":
    pytest.main([__file__])
