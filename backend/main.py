"""
FastAPI backend for the School Scheduler application.
Integrates with the existing ImprovedSchoolScheduler algorithm.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import sys
import json
from datetime import datetime
import traceback

# Add the parent directory to the path to import the scheduler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery_app, generate_schedule_task
from models import ScheduleRequest, ScheduleResponse, TaskStatus

app = FastAPI(
    title="School Scheduler API",
    description="API for generating school schedules with professor assignments",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (use Redis/DB in production)
schedule_results = {}

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "School Scheduler API is running!", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    try:
        # Test Celery connection
        celery_status = celery_app.control.inspect().stats()
        celery_healthy = celery_status is not None
    except Exception:
        celery_healthy = False
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "celery": "connected" if celery_healthy else "disconnected",
        "services": {
            "api": "running",
            "celery": "connected" if celery_healthy else "disconnected"
        }
    }

@app.post("/api/schedule/generate")
async def generate_schedule(request: ScheduleRequest):
    """
    Start schedule generation process.
    Returns a task ID for tracking progress.
    """
    try:
        # Start the background task
        task = generate_schedule_task.delay(
            csv_file_path=request.csv_file_path,
            constraints=request.constraints,
            options=request.options
        )
        
        # Store initial status
        schedule_results[task.id] = {
            "task_id": task.id,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "message": "Schedule generation started..."
        }
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "Schedule generation started. This will take 2-3 minutes.",
            "estimated_completion": "2-3 minutes"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start schedule generation: {str(e)}"
        )

@app.get("/api/schedule/status/{task_id}")
async def get_schedule_status(task_id: str):
    """
    Get the status of a schedule generation task.
    """
    try:
        # Get task result from Celery
        task = celery_app.AsyncResult(task_id)
        
        result = {
            "task_id": task_id,
            "status": task.status,
        }
        
        if task.status == "PENDING":
            result.update({
                "message": "Schedule generation in progress...",
                "progress": 25,  # Estimated progress
            })
        elif task.status == "PROGRESS":
            # Custom status for progress updates
            if task.info:
                result.update(task.info)
        elif task.status == "SUCCESS":
            result.update({
                "message": "Schedule generated successfully!",
                "progress": 100,
                "result": task.result,
                "completed_at": datetime.now().isoformat()
            })
        elif task.status == "FAILURE":
            result.update({
                "message": f"Schedule generation failed: {str(task.info)}",
                "progress": 0,
                "error": str(task.info)
            })
        
        # Update local storage
        schedule_results[task_id] = result
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )

@app.get("/api/schedule/result/{task_id}")
async def get_schedule_result(task_id: str):
    """
    Get the final schedule result.
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.status != "SUCCESS":
            raise HTTPException(
                status_code=400,
                detail=f"Task not completed. Current status: {task.status}"
            )
        
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task.result,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schedule result: {str(e)}"
        )

@app.get("/api/schedules")
async def list_schedules():
    """
    List all generated schedules.
    """
    return {
        "schedules": [
            {
                "task_id": task_id,
                "status": result.get("status"),
                "created_at": result.get("created_at"),
                "completed_at": result.get("completed_at"),
                "message": result.get("message")
            }
            for task_id, result in schedule_results.items()
        ]
    }

@app.delete("/api/schedule/{task_id}")
async def delete_schedule(task_id: str):
    """
    Delete a schedule result.
    """
    if task_id in schedule_results:
        del schedule_results[task_id]
        return {"message": f"Schedule {task_id} deleted successfully"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule {task_id} not found"
        )

# Additional endpoints for file management
@app.get("/api/files/csv")
async def list_csv_files():
    """
    List available CSV files for schedule generation.
    """
    try:
        # Look for CSV files in the data directory and root
        csv_files = []
        
        # Check parent directory (where your CSV files are)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for file in os.listdir(parent_dir):
            if file.endswith('.csv'):
                csv_files.append({
                    "name": file,
                    "path": os.path.join(parent_dir, file),
                    "location": "root"
                })
        
        # Check data directory
        data_dir = os.path.join(parent_dir, "data")
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.csv'):
                    csv_files.append({
                        "name": file,
                        "path": os.path.join(data_dir, file),
                        "location": "data"
                    })
        
        return {"csv_files": csv_files}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list CSV files: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)