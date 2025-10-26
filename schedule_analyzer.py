import pandas as pd
from collections import Counter

class ScheduleAnalyzer:
    def __init__(self, teacher_schedule_path, class_schedule_path):
        """Initialize the analyzer with schedule CSV files."""
        self.teacher_df = pd.read_csv(teacher_schedule_path, index_col=0)
        self.class_df = pd.read_csv(class_schedule_path, index_col=0)
        
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.hours = list(range(8, 15))
        
    def analyze_teacher_workload(self):
        """Analyze teacher workload distribution."""
        print("=== TEACHER WORKLOAD ANALYSIS ===")
        
        # Get weekly totals
        weekly_totals = self.teacher_df['Weekly_Total']
        
        # Basic statistics
        print(f"Number of teachers: {len(weekly_totals)}")
        print(f"Average hours per teacher: {weekly_totals.mean():.1f}")
        print(f"Median hours per teacher: {weekly_totals.median():.1f}")
        print(f"Standard deviation: {weekly_totals.std():.1f}")
        
        # Workload categories
        underloaded = weekly_totals[weekly_totals < 10]
        normal_load = weekly_totals[(weekly_totals >= 10) & (weekly_totals <= 20)]
        overloaded = weekly_totals[weekly_totals > 20]
        
        print(f"\nWorkload distribution:")
        print(f"  Underloaded (<10h): {len(underloaded)} teachers ({len(underloaded)/len(weekly_totals)*100:.1f}%)")
        print(f"  Normal load (10-20h): {len(normal_load)} teachers ({len(normal_load)/len(weekly_totals)*100:.1f}%)")
        print(f"  Overloaded (>20h): {len(overloaded)} teachers ({len(overloaded)/len(weekly_totals)*100:.1f}%)")
        
        # Top 10 busiest teachers
        print(f"\nTop 10 busiest teachers:")
        top_teachers = weekly_totals.sort_values(ascending=False).head(10)
        for teacher, hours in top_teachers.items():
            print(f"  {teacher}: {hours} hours/week")
            
        # Teachers with 0 hours
        idle_teachers = weekly_totals[weekly_totals == 0]
        if len(idle_teachers) > 0:
            print(f"\nTeachers with no assigned hours ({len(idle_teachers)}):")
            for teacher in idle_teachers.index:
                print(f"  {teacher}")
        
        return weekly_totals
    
    def analyze_class_schedule(self):
        """Analyze class schedule distribution."""
        print("\n=== CLASS SCHEDULE ANALYSIS ===")
        
        # Get weekly totals
        weekly_totals = self.class_df['Weekly_Total']
        
        print(f"Number of classes: {len(weekly_totals)}")
        print(f"Average hours per class: {weekly_totals.mean():.1f}")
        print(f"Range: {weekly_totals.min()} - {weekly_totals.max()} hours")
        
        # Classes with less than 30 hours
        incomplete = weekly_totals[weekly_totals < 30]
        if len(incomplete) > 0:
            print(f"\nClasses with incomplete schedules ({len(incomplete)}):")
            for class_name, hours in incomplete.sort_values().items():
                print(f"  {class_name}: {hours}/30 hours ({(30-hours)} missing)")
        else:
            print("\nAll classes have complete 30-hour schedules!")
            
        return weekly_totals
    
    def analyze_daily_distribution(self):
        """Analyze how classes are distributed across days."""
        print("\n=== DAILY DISTRIBUTION ANALYSIS ===")
        
        daily_counts = {}
        for day in self.days:
            day_columns = [col for col in self.class_df.columns if col.startswith(day) and 'total' not in col]
            day_classes = 0
            for col in day_columns:
                day_classes += (self.class_df[col] != '').sum()
            daily_counts[day] = day_classes
            
        for day, count in daily_counts.items():
            print(f"  {day}: {count} class sessions")
            
        # Check for day balance
        min_day = min(daily_counts.values())
        max_day = max(daily_counts.values())
        balance = max_day - min_day
        print(f"\nDaily balance: {balance} sessions difference between busiest and quietest days")
        
        return daily_counts
    
    def analyze_hourly_distribution(self):
        """Analyze how classes are distributed across hours."""
        print("\n=== HOURLY DISTRIBUTION ANALYSIS ===")
        
        hourly_counts = {}
        for hour in self.hours:
            hour_str = f"{hour:02d}h"
            hour_classes = 0
            for day in self.days:
                col = f"{day}_{hour_str}"
                if col in self.class_df.columns:
                    hour_classes += (self.class_df[col] != '').sum()
            hourly_counts[hour] = hour_classes
            
        for hour, count in hourly_counts.items():
            print(f"  {hour:02d}:00: {count} class sessions")
            
        # Identify peak and off-peak hours
        peak_hour = max(hourly_counts.keys(), key=lambda x: hourly_counts[x])
        quiet_hour = min(hourly_counts.keys(), key=lambda x: hourly_counts[x])
        
        print(f"\nPeak hour: {peak_hour:02d}:00 ({hourly_counts[peak_hour]} sessions)")
        print(f"Quietest hour: {quiet_hour:02d}:00 ({hourly_counts[quiet_hour]} sessions)")
        
        return hourly_counts
    
    def analyze_subject_distribution(self):
        """Analyze subject distribution across the schedule."""
        print("\n=== SUBJECT DISTRIBUTION ANALYSIS ===")
        
        # Extract subjects from class schedule
        subjects = []
        for col in self.class_df.columns:
            if not col.endswith('_total') and col != 'Weekly_Total':
                for entry in self.class_df[col]:
                    if entry and entry != '' and isinstance(entry, str):
                        # Extract subject from "TEACHER(SUBJECT)" format
                        if '(' in entry and ')' in entry:
                            subject = entry.split('(')[1].split(')')[0]
                            subjects.append(subject)
        
        subject_counts = Counter(subjects)
        total_sessions = sum(subject_counts.values())
        
        print(f"Total subject sessions: {total_sessions}")
        print(f"Number of different subjects: {len(subject_counts)}")
        
        print(f"\nTop 10 most scheduled subjects:")
        for subject, count in subject_counts.most_common(10):
            percentage = (count / total_sessions) * 100
            print(f"  {subject}: {count} sessions ({percentage:.1f}%)")
            
        return subject_counts
    
    def find_scheduling_conflicts(self):
        """Find potential scheduling conflicts or issues."""
        print("\n=== POTENTIAL ISSUES ANALYSIS ===")
        
        conflicts = []
        
        # Check for teachers teaching multiple classes at the same time
        for day in self.days:
            for hour in self.hours:
                hour_str = f"{hour:02d}h"
                col = f"{day}_{hour_str}"
                
                if col in self.class_df.columns:
                    teachers_this_slot = []
                    for entry in self.class_df[col]:
                        if entry and entry != '' and isinstance(entry, str):
                            if '(' in entry:
                                teacher = entry.split('(')[0]
                                teachers_this_slot.append(teacher)
                    
                    # Find duplicate teachers
                    teacher_counts = Counter(teachers_this_slot)
                    for teacher, count in teacher_counts.items():
                        if count > 1:
                            conflicts.append(f"{day} {hour:02d}:00 - {teacher} teaching {count} classes simultaneously")
        
        if conflicts:
            print(f"Found {len(conflicts)} potential conflicts:")
            for conflict in conflicts[:10]:  # Show first 10
                print(f"  {conflict}")
            if len(conflicts) > 10:
                print(f"  ... and {len(conflicts) - 10} more")
        else:
            print("No scheduling conflicts detected!")
        
        # Check for classes with gaps in their schedule
        print(f"\nChecking for schedule gaps...")
        gaps_found = 0
        for class_name in self.class_df.index:
            for day in self.days:
                day_schedule = []
                for hour in self.hours:
                    hour_str = f"{hour:02d}h"
                    col = f"{day}_{hour_str}"
                    if col in self.class_df.columns:
                        entry = self.class_df.loc[class_name, col]
                        day_schedule.append(entry != '' and entry is not None and pd.notna(entry))
                
                # Look for gaps (False between True values)
                if any(day_schedule):  # If there are any classes this day
                    first_class = next(i for i, x in enumerate(day_schedule) if x)
                    last_class = len(day_schedule) - 1 - next(i for i, x in enumerate(reversed(day_schedule)) if x)
                    
                    for i in range(first_class + 1, last_class):
                        if not day_schedule[i]:
                            gaps_found += 1
                            print(f"  {class_name} has gap on {day} at {(8+i):02d}:00")
                            
        print(f"Total schedule gaps found: {gaps_found}")
        
        return conflicts
    
    def create_visual_summary(self, save_path='./'):
        """Create visual summaries of the schedule."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Set up the plot style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('School Schedule Analysis', fontsize=16)
            
            # 1. Teacher workload distribution
            ax1 = axes[0, 0]
            weekly_totals = self.teacher_df['Weekly_Total']
            ax1.hist(weekly_totals, bins=15, alpha=0.7, edgecolor='black')
            ax1.set_title('Teacher Workload Distribution')
            ax1.set_xlabel('Hours per week')
            ax1.set_ylabel('Number of teachers')
            ax1.axvline(weekly_totals.mean(), color='red', linestyle='--', label=f'Mean: {weekly_totals.mean():.1f}h')
            ax1.legend()
            
            # 2. Daily class distribution
            ax2 = axes[0, 1]
            daily_counts = {}
            for day in self.days:
                day_columns = [col for col in self.class_df.columns if col.startswith(day) and 'total' not in col]
                day_classes = 0
                for col in day_columns:
                    day_classes += (self.class_df[col] != '').sum()
                daily_counts[day] = day_classes
            
            ax2.bar(daily_counts.keys(), daily_counts.values(), alpha=0.7)
            ax2.set_title('Daily Class Distribution')
            ax2.set_xlabel('Day of week')
            ax2.set_ylabel('Number of class sessions')
            ax2.tick_params(axis='x', rotation=45)
            
            # 3. Hourly class distribution
            ax3 = axes[1, 0]
            hourly_counts = {}
            for hour in self.hours:
                hour_str = f"{hour:02d}h"
                hour_classes = 0
                for day in self.days:
                    col = f"{day}_{hour_str}"
                    if col in self.class_df.columns:
                        hour_classes += (self.class_df[col] != '').sum()
                hourly_counts[hour] = hour_classes
            
            ax3.bar([f"{h:02d}:00" for h in hourly_counts.keys()], hourly_counts.values(), alpha=0.7)
            ax3.set_title('Hourly Class Distribution')
            ax3.set_xlabel('Hour of day')
            ax3.set_ylabel('Number of class sessions')
            ax3.tick_params(axis='x', rotation=45)
            
            # 4. Class schedule completion
            ax4 = axes[1, 1]
            class_totals = self.class_df['Weekly_Total']
            completion_rates = (class_totals / 30) * 100
            ax4.hist(completion_rates, bins=10, alpha=0.7, edgecolor='black')
            ax4.set_title('Class Schedule Completion')
            ax4.set_xlabel('Completion percentage')
            ax4.set_ylabel('Number of classes')
            ax4.axvline(completion_rates.mean(), color='red', linestyle='--', label=f'Mean: {completion_rates.mean():.1f}%')
            ax4.legend()
            
            plt.tight_layout()
            
            # Save the plot
            plot_path = f"{save_path}schedule_analysis.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"\nVisual summary saved to: {plot_path}")
            
            plt.show()
            
        except ImportError:
            print("\nMatplotlib/Seaborn not available for visual summaries")
            print("Install with: pip install matplotlib seaborn")
    
    def generate_full_report(self, save_path='./'):
        """Generate a comprehensive analysis report."""
        print("COMPREHENSIVE SCHEDULE ANALYSIS REPORT")
        print("="*50)
        
        # Run all analyses
        self.analyze_teacher_workload()
        self.analyze_class_schedule()
        self.analyze_daily_distribution()
        self.analyze_hourly_distribution()
        self.analyze_subject_distribution()
        self.find_scheduling_conflicts()
        
        # Try to create visual summary
        self.create_visual_summary(save_path)
        
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")

# Usage example
def main():
    analyzer = ScheduleAnalyzer(
        '/Users/juan/Projects/oraccio/improved_teacher_schedule.csv',
        '/Users/juan/Projects/oraccio/improved_class_schedule.csv'
    )
    
    analyzer.generate_full_report('/Users/juan/Projects/oraccio/')
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()