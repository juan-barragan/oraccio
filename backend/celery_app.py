"""
Celery configuration for background task processing.
"""

from celery import Celery
import os
import sys
import json
from typing import Dict, Any, Optional
import traceback
from datetime import datetime

# Add the parent directory to the path to import the scheduler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your scheduler wrapper
try:
    from scheduler_wrapper import create_scheduler
except ImportError as e:
    print(f"Warning: Could not import scheduler wrapper: {e}")
    create_scheduler = None

# Celery configuration
celery_app = Celery(
    'scheduler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['celery_app']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_routes={
        'celery_app.generate_schedule_task': {'queue': 'schedule_generation'},
    }
)

def update_task_progress(task_id: str, progress: int, message: str):
    """Helper function to update task progress."""
    celery_app.backend.store_result(
        task_id,
        {'progress': progress, 'message': message},
        'PROGRESS'
    )

@celery_app.task(bind=True)
def generate_schedule_task(self, csv_file_path: str, constraints: Dict[str, Any] = None, options: Dict[str, Any] = None):
    """
    Background task to generate school schedule using your improved scheduler.
    This task will run for 2-3 minutes.
    """
    task_id = self.request.id
    
    try:
        # Update progress: Starting
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': 'Initializing scheduler...', 'stage': 'initialization'}
        )
        
        if create_scheduler is None:
            raise Exception("Scheduler wrapper not available")
        
        # Initialize the scheduler wrapper
        scheduler = create_scheduler(csv_file_path)
        
        # Update progress: Loading data
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'message': 'Loading and validating data...', 'stage': 'data_loading'}
        )
        
        # Apply custom constraints if provided
        if constraints:
            # You can extend this to apply custom constraints
            pass
        
        # Update progress: Starting algorithm
        self.update_state(
            state='PROGRESS',
            meta={'progress': 30, 'message': 'Starting schedule generation algorithm...', 'stage': 'algorithm_start'}
        )
        
        # Run the main scheduling algorithm
        # This is where your 2-3 minute algorithm runs
        success = scheduler.generate_schedule()
        
        # Update progress: Algorithm completed
        self.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'message': 'Algorithm completed, preparing results...', 'stage': 'post_processing'}
        )
        
        if not success:
            raise Exception("Schedule generation failed - algorithm could not find a valid solution")
        
        # Convert results to JSON-serializable format
        teacher_schedule = scheduler.export_teacher_schedule()
        class_schedule = scheduler.export_class_schedule()
        
        # Update progress: Finalizing
        self.update_state(
            state='PROGRESS',
            meta={'progress': 95, 'message': 'Finalizing and validating results...', 'stage': 'finalization'}
        )
        
        # Prepare the final result
        result = {
            'success': True,
            'teacher_schedule': teacher_schedule,
            'class_schedule': class_schedule,
            'statistics': {
                'total_teachers': len(teacher_schedule),
                'total_classes': len(class_schedule) if class_schedule else 0,
                'generation_time': '2-3 minutes',  # You can track actual time
                'algorithm_version': 'ImprovedScheduler v1.0'
            },
            'metadata': {
                'csv_file': csv_file_path,
                'generated_at': datetime.now().isoformat(),
                'constraints_applied': constraints or {},
                'options_used': options or {}
            }
        }
        
        return result
        
    except Exception as e:
        # Log the full error for debugging
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'task_id': task_id,
            'csv_file_path': csv_file_path
        }
        
        print(f"Schedule generation failed: {error_details}")
        
        # Update task state to failure
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'details': error_details}
        )
        
        raise Exception(f"Schedule generation failed: {str(e)}")

@celery_app.task
def test_task():
    """Simple test task to verify Celery is working."""
    return {"message": "Celery is working!", "timestamp": datetime.now().isoformat()}

# Health check task
@celery_app.task
def health_check():
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "worker": "active"
    }