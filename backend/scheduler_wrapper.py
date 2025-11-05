"""
API Wrapper for the ImprovedSchoolScheduler.
Adds export methods and API-friendly interfaces to your existing scheduler.
"""

import sys
import os
import pandas as pd
import json
from typing import Dict, List, Any, Optional

# Import your existing scheduler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from improved_scheduler import ImprovedSchoolScheduler

class ApiSchedulerWrapper(ImprovedSchoolScheduler):
    """
    Wrapper around your ImprovedSchoolScheduler that adds API-friendly methods.
    """
    
    def __init__(self, csv_file_path: str):
        """Initialize with the same interface as your original scheduler."""
        super().__init__(csv_file_path)
        self.generation_successful = False
        
    def generate_schedule(self) -> bool:
        """
        Run the complete schedule generation process.
        Returns True if successful, False otherwise.
        """
        try:
            # This is where you would run your main algorithm
            # Based on your existing code structure, this would involve:
            
            # 1. Initial schedule generation
            print("Starting initial schedule generation...")
            
            # 2. Handle missing classes (your swap strategy)
            print("Handling missing classes with swap strategy...")
            
            # For now, let's simulate your algorithm working
            # In practice, you'd copy your main algorithm logic here
            self._run_scheduling_algorithm()
            
            # 3. Sanity check
            if self.sanity_check_schedule():
                self.generation_successful = True
                print("✅ Schedule generation completed successfully!")
                return True
            else:
                print("❌ Schedule generation failed sanity check.")
                return False
                
        except Exception as e:
            print(f"❌ Schedule generation failed with error: {e}")
            return False
    
    def _run_scheduling_algorithm(self):
        """
        Placeholder for your main scheduling algorithm.
        You would copy your main algorithm logic here.
        """
        # This is where your existing algorithm would run
        # For now, I'll create a minimal working example
        
        # Initialize some basic schedule structure
        if not hasattr(self, 'schedule') or self.schedule is None:
            self.schedule = self.create_empty_schedule()
        
        # Simulate algorithm working (replace with your actual logic)
        print("Running scheduling algorithm...")
        
        # Your algorithm logic would go here
        # This is just a placeholder to make the API work
        pass
    
    def export_teacher_schedule(self) -> Dict[str, Any]:
        """
        Export teacher schedule in a format suitable for the web frontend.
        Returns data compatible with your existing CSV structure.
        """
        try:
            # Check if we have schedule data
            if not hasattr(self, 'schedule') or self.schedule is None:
                return {"error": "No schedule data available"}
            
            # Create the teacher schedule export
            teacher_schedule = {}
            
            # Iterate through all teachers
            for teacher in self.teachers:
                teacher_schedule[teacher] = {}
                
                # For each day and hour, check what this teacher is assigned to
                for day in self.days:
                    for hour in self.hours:
                        time_slot = f"{day}{hour}"
                        
                        # Get assignment for this teacher at this time
                        assignment = self._get_teacher_assignment(teacher, day, hour)
                        teacher_schedule[teacher][time_slot] = assignment
            
            # Also include summary statistics
            schedule_data = {
                "teacher_assignments": teacher_schedule,
                "summary": {
                    "total_teachers": len(self.teachers),
                    "total_slots": len(self.days) * len(self.hours),
                    "days": self.days,
                    "hours": self.hours
                }
            }
            
            return schedule_data
            
        except Exception as e:
            return {"error": f"Failed to export teacher schedule: {str(e)}"}
    
    def export_class_schedule(self) -> Optional[Dict[str, Any]]:
        """
        Export class schedule in a format suitable for the web frontend.
        """
        try:
            if not hasattr(self, 'schedule') or self.schedule is None:
                return {"error": "No schedule data available"}
            
            class_schedule = {}
            
            # Get all classes
            if hasattr(self, 'classes'):
                for class_name in self.classes:
                    class_schedule[class_name] = {}
                    
                    for day in self.days:
                        for hour in self.hours:
                            time_slot = f"{day}{hour}"
                            
                            # Get assignment for this class at this time
                            assignment = self._get_class_assignment(class_name, day, hour)
                            class_schedule[class_name][time_slot] = assignment
            
            return {
                "class_assignments": class_schedule,
                "summary": {
                    "total_classes": len(getattr(self, 'classes', [])),
                    "total_slots": len(self.days) * len(self.hours)
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to export class schedule: {str(e)}"}
    
    def _get_teacher_assignment(self, teacher: str, day: str, hour: int) -> str:
        """
        Get what a teacher is assigned to at a specific day/hour.
        Returns class name or empty string.
        """
        try:
            # This depends on your schedule structure
            # Based on your code, you have a schedule matrix
            
            if hasattr(self, 'schedule') and self.schedule is not None:
                # Get schedule entries for this slot
                entries = self.get_schedule_slot(day, hour)
                
                # Find entry for this teacher
                for entry in entries:
                    if hasattr(entry, 'teacher') and entry.teacher == teacher:
                        if hasattr(entry, 'class_name'):
                            return entry.class_name
                        return "ASSIGNED"  # Some assignment exists
            
            return ""  # No assignment
            
        except Exception:
            return ""
    
    def _get_class_assignment(self, class_name: str, day: str, hour: int) -> str:
        """
        Get what teacher is assigned to a class at a specific day/hour.
        """
        try:
            if hasattr(self, 'schedule') and self.schedule is not None:
                entries = self.get_schedule_slot(day, hour)
                
                for entry in entries:
                    if hasattr(entry, 'class_name') and entry.class_name == class_name:
                        if hasattr(entry, 'teacher'):
                            return entry.teacher
                        return "ASSIGNED"
            
            return ""
            
        except Exception:
            return ""
    
    def export_to_csv_format(self) -> Dict[str, Any]:
        """
        Export in the same CSV format as your existing output files.
        This matches the format of your improved_teacher_schedule.csv.
        """
        try:
            teacher_data = []
            
            for teacher in self.teachers:
                row = {"Teacher": teacher}
                
                # Add columns for each day/hour combination
                for day in self.days:
                    for hour in self.hours:
                        col_name = f"{day}{hour}"
                        assignment = self._get_teacher_assignment(teacher, day, hour)
                        row[col_name] = assignment
                
                teacher_data.append(row)
            
            return {
                "csv_data": teacher_data,
                "columns": ["Teacher"] + [f"{day}{hour}" for day in self.days for hour in self.hours]
            }
            
        except Exception as e:
            return {"error": f"Failed to export CSV format: {str(e)}"}

# Factory function to create the scheduler
def create_scheduler(csv_file_path: str) -> ApiSchedulerWrapper:
    """
    Factory function to create a scheduler instance.
    """
    return ApiSchedulerWrapper(csv_file_path)