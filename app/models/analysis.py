"""
Analysis models for stock analysis functionality.
"""

from datetime import datetime
from typing import List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, 
    Boolean, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

class AnalysisType(enum.Enum):
    """Types of analysis that can be performed."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    PRICE_PREDICTION = "price_prediction"
    PATTERN_RECOGNITION = "pattern_recognition"
    ANOMALY_DETECTION = "anomaly_detection"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    CUSTOM = "custom"

class AnalysisStatus(enum.Enum):
    """Status of an analysis run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnalysisInput(Base, TimestampMixin, UUIDMixin):
    """Model for storing analysis input parameters."""
    __tablename__ = "analysis_inputs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    parameter_name = Column(String, nullable=False)
    parameter_value = Column(JSON, nullable=False)
    parameter_type = Column(String, nullable=False)  # e.g., "string", "number", "array", etc.

    # Relationships
    analysis = relationship("Analysis", back_populates="inputs")

    def __repr__(self):
        return f"<AnalysisInput(id={self.id}, parameter='{self.parameter_name}')>"

class AnalysisResult(Base, TimestampMixin, UUIDMixin):
    """Model for storing analysis results."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    result_type = Column(String, nullable=False)
    result_data = Column(JSON, nullable=False)
    confidence_score = Column(Float)
    result_metadata = Column(JSON)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="results")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, type='{self.result_type}')>"

class AnalysisRun(Base, TimestampMixin, UUIDMixin):
    """Model for tracking individual analysis execution runs."""
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    error_message = Column(String)
    execution_metadata = Column(JSON)

    # Relationships
    analysis = relationship("Analysis", back_populates="runs")
    results = relationship("AnalysisResult", back_populates="analysis_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisRun(id={self.id}, status='{self.status}')>"

class Analysis(Base, TimestampMixin, UUIDMixin):
    """Primary model for stock analysis."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    analysis_type = Column(SQLEnum(AnalysisType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    schedule = Column(JSON)  # For scheduled/recurring analyses
    configuration = Column(JSON)  # Additional configuration options

    # Relationships
    user = relationship("User", backref="analyses")
    inputs = relationship("AnalysisInput", back_populates="analysis", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="analysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Analysis(id={self.id}, name='{self.name}', type='{self.analysis_type}')>"

    def get_latest_run(self) -> AnalysisRun:
        """Get the most recent analysis run."""
        if not self.runs:
            return None
        return max(self.runs, key=lambda r: r.created_at)

    def get_successful_runs(self) -> List[AnalysisRun]:
        """Get all successful analysis runs."""
        return [run for run in self.runs if run.status == AnalysisStatus.COMPLETED]
