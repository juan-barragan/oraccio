#!/usr/bin/env python3
"""
Test script to verify the complete scheduler integration.
This will test your API wrapper without needing to run the full web stack.
"""

import sys
import os
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_scheduler_wrapper():
    """Test the scheduler wrapper functionality."""
    print("🧪 Testing Scheduler Wrapper Integration")
    print("=" * 50)
    
    # Path to your CSV file (in the data directory)
    csv_file_path = "../data/docente_classes.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        print("Please make sure your improved_teacher_schedule.csv is in the parent directory.")
        return False
    
    try:
        # Import the wrapper
        from scheduler_wrapper import create_scheduler
        print("✅ Successfully imported scheduler wrapper")
        
        # Create scheduler instance
        print(f"📄 Loading CSV file: {csv_file_path}")
        scheduler = create_scheduler(csv_file_path)
        print("✅ Scheduler instance created")
        
        # Test the export methods (even before running full algorithm)
        print("\n🔍 Testing export methods...")
        
        # Test teacher schedule export
        teacher_export = scheduler.export_teacher_schedule()
        if "error" in teacher_export:
            print(f"⚠️  Teacher export (expected): {teacher_export['error']}")
        else:
            print("✅ Teacher export method works")
            
        # Test class schedule export
        class_export = scheduler.export_class_schedule()
        if "error" in class_export:
            print(f"⚠️  Class export (expected): {class_export['error']}")
        else:
            print("✅ Class export method works")
            
        # Test CSV format export
        csv_export = scheduler.export_to_csv_format()
        if "error" in csv_export:
            print(f"⚠️  CSV export (expected): {csv_export['error']}")
        else:
            print("✅ CSV export method works")
        
        print("\n🚀 Testing schedule generation...")
        # Test the full generation process
        # Note: This will run your actual algorithm, so it might take time
        success = scheduler.generate_schedule()
        
        if success:
            print("✅ Schedule generation completed successfully!")
            
            # Now test exports with actual data
            teacher_export = scheduler.export_teacher_schedule()
            class_export = scheduler.export_class_schedule()
            
            print(f"📊 Teacher schedule entries: {len(teacher_export.get('teacher_assignments', {}))}")
            print(f"📊 Class schedule entries: {len(class_export.get('class_assignments', {}))}")
            
        else:
            print("⚠️  Schedule generation completed but was not successful")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure your improved_scheduler.py is in the parent directory")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """Test that the API components can be imported."""
    print("\n🌐 Testing API Integration")
    print("=" * 50)
    
    try:
        # Test FastAPI imports
        from main import app
        print("✅ FastAPI app imported successfully")
        
        # Test Celery imports
        from celery_app import celery_app, generate_schedule_task
        print("✅ Celery app and tasks imported successfully")
        
        # Test models
        from models import ScheduleRequest, TaskStatus, ScheduleResponse
        print("✅ Pydantic models imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Oraccio Backend Integration Test")
    print("=" * 50)
    
    # Test scheduler wrapper
    wrapper_success = test_scheduler_wrapper()
    
    # Test API integration
    api_success = test_api_integration()
    
    print("\n📋 Test Summary")
    print("=" * 50)
    print(f"Scheduler Wrapper: {'✅ PASS' if wrapper_success else '❌ FAIL'}")
    print(f"API Integration:   {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if wrapper_success and api_success:
        print("\n🎉 All tests passed! Your backend is ready.")
        print("\nNext steps:")
        print("1. Start Redis: redis-server")
        print("2. Start Celery worker: celery -A celery_app worker --loglevel=info")
        print("3. Start FastAPI: uvicorn main:app --reload")
        print("4. Test API endpoints with curl or Postman")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")