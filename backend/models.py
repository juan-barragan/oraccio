"""
Pydantic models for API request and response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class ScheduleRequest(BaseModel):
    """Request model for schedule generation."""
    csv_file_path: str = Field(..., description="Path to the CSV file containing teacher/class data")
    constraints: Optional[Dict[str, Any]] = Field(default={}, description="Custom constraints for schedule generation")
    options: Optional[Dict[str, Any]] = Field(default={}, description="Additional options for the algorithm")
    
    class Config:
        schema_extra = {
            "example": {
                "csv_file_path": "/path/to/conseil_docente_cleaned.csv",
                "constraints": {
                    "max_daily_hours": 5,
                    "min_break_time": 1
                },
                "options": {
                    "optimization_level": "high",
                    "allow_gaps": True
                }
            }
        }

class TaskStatus(BaseModel):
    """Model for task status response."""
    task_id: str
    status: str = Field(..., description="Task status: PENDING, PROGRESS, SUCCESS, FAILURE")
    progress: Optional[int] = Field(default=0, ge=0, le=100, description="Progress percentage (0-100)")
    message: Optional[str] = Field(default="", description="Current status message")
    stage: Optional[str] = Field(default="", description="Current processing stage")
    created_at: Optional[str] = Field(default="", description="Task creation timestamp")
    completed_at: Optional[str] = Field(default="", description="Task completion timestamp")
    error: Optional[str] = Field(default="", description="Error message if failed")

class ScheduleStatistics(BaseModel):
    """Statistics about the generated schedule."""
    total_teachers: int = Field(..., description="Total number of teachers in schedule")
    total_classes: int = Field(..., description="Total number of classes in schedule")
    generation_time: str = Field(..., description="Time taken to generate schedule")
    algorithm_version: str = Field(..., description="Version of the scheduling algorithm")

class ScheduleMetadata(BaseModel):
    """Metadata about the schedule generation."""
    csv_file: str = Field(..., description="Source CSV file path")
    generated_at: str = Field(..., description="Generation timestamp")
    constraints_applied: Dict[str, Any] = Field(default={}, description="Constraints that were applied")
    options_used: Dict[str, Any] = Field(default={}, description="Options that were used")

class ScheduleResponse(BaseModel):
    """Response model for completed schedule generation."""
    success: bool = Field(..., description="Whether schedule generation was successful")
    teacher_schedule: Dict[str, Any] = Field(..., description="Generated teacher schedule data")
    class_schedule: Optional[Dict[str, Any]] = Field(default=None, description="Generated class schedule data")
    statistics: ScheduleStatistics = Field(..., description="Generation statistics")
    metadata: ScheduleMetadata = Field(..., description="Generation metadata")

class TeacherScheduleEntry(BaseModel):
    """Individual entry in teacher schedule."""
    teacher_name: str
    day: str = Field(..., pattern="^(LUN|MAR|MER|GIO|VEN)$")
    hour: int = Field(..., ge=8, le=14)
    class_name: Optional[str] = None
    subject: Optional[str] = None

class ClassScheduleEntry(BaseModel):
    """Individual entry in class schedule."""
    class_name: str
    day: str = Field(..., pattern="^(LUN|MAR|MER|GIO|VEN)$")
    hour: int = Field(..., ge=8, le=14)
    teacher_name: Optional[str] = None
    subject: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall system status")
    timestamp: str = Field(..., description="Health check timestamp")
    celery: str = Field(..., description="Celery connection status")
    services: Dict[str, str] = Field(..., description="Individual service statuses")

class FileInfo(BaseModel):
    """Information about available files."""
    name: str = Field(..., description="File name")
    path: str = Field(..., description="Full file path")
    location: str = Field(..., description="File location (root, data, etc.)")

class FileListResponse(BaseModel):
    """Response for file listing."""
    csv_files: List[FileInfo] = Field(..., description="Available CSV files")

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error description")
    error_type: Optional[str] = Field(default="", description="Type of error")
    timestamp: Optional[str] = Field(default="", description="Error timestamp")

class ScheduleListResponse(BaseModel):
    """Response for listing schedules."""
    schedules: List[Dict[str, Any]] = Field(..., description="List of generated schedules")

# Request models for different endpoints
class SimpleTaskRequest(BaseModel):
    """Simple task request for testing."""
    message: Optional[str] = Field(default="test", description="Test message")

class DeleteScheduleResponse(BaseModel):
    """Response for schedule deletion."""
    message: str = Field(..., description="Deletion confirmation message")
    
# Additional models for future features
class ConstraintRule(BaseModel):
    """Individual constraint rule."""
    rule_type: str = Field(..., description="Type of constraint rule")
    parameters: Dict[str, Any] = Field(..., description="Rule parameters")
    priority: int = Field(default=1, ge=1, le=10, description="Rule priority (1-10)")

class AdvancedScheduleRequest(ScheduleRequest):
    """Extended schedule request with advanced options."""
    constraint_rules: Optional[List[ConstraintRule]] = Field(default=[], description="Advanced constraint rules")
    optimization_goals: Optional[List[str]] = Field(default=[], description="Optimization objectives")
    teacher_preferences: Optional[Dict[str, Any]] = Field(default={}, description="Teacher-specific preferences")
    class_requirements: Optional[Dict[str, Any]] = Field(default={}, description="Class-specific requirements")