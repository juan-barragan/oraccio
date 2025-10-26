import ast
import re
import pandas as pd
from typing import List, Tuple

def parse_failed_assignments(file_path: str) -> List[Tuple[str, str, str, int, int]]:
    """
    Parse the failed.txt file to recover a list of tuples.
    
    Args:
        file_path: Path to the failed.txt file
        
    Returns:
        List of tuples containing (teacher, class, subject, remaining_hours, allocated_hours)
    """
    failed_assignments = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # Use ast.literal_eval to safely parse the tuple string
                    parsed_tuple = ast.literal_eval(line)
                    
                    # Validate that it's a tuple with 5 elements
                    if isinstance(parsed_tuple, tuple) and len(parsed_tuple) == 5:
                        teacher, class_name, subject, remaining_hours, allocated_hours = parsed_tuple
                        
                        # Validate types
                        if (isinstance(teacher, str) and 
                            isinstance(class_name, str) and 
                            isinstance(subject, str) and 
                            isinstance(remaining_hours, int) and 
                            isinstance(allocated_hours, int)):
                            
                            failed_assignments.append(parsed_tuple)
                        else:
                            print(f"Warning: Invalid data types in line {line_num}: {line}")
                    else:
                        print(f"Warning: Invalid tuple format in line {line_num}: {line}")
                        
                except (ValueError, SyntaxError) as e:
                    print(f"Warning: Could not parse line {line_num}: {line}")
                    print(f"Error: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []
    
    return failed_assignments

def parse_failed_assignments_regex(file_path: str) -> List[Tuple[str, str, str, int, int]]:
    """
    Alternative parser using regex for more robust parsing.
    
    Args:
        file_path: Path to the failed.txt file
        
    Returns:
        List of tuples containing (teacher, class, subject, remaining_hours, allocated_hours)
    """
    failed_assignments = []
    
    # Regex pattern to match tuple format: ('text', 'text', 'text', number, number)
    pattern = r"\('([^']+)', '([^']+)', '([^']+)', (\d+), (\d+)\)"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                    
                match = re.match(pattern, line)
                if match:
                    teacher = match.group(1)
                    class_name = match.group(2)
                    subject = match.group(3)
                    remaining_hours = int(match.group(4))
                    allocated_hours = int(match.group(5))
                    
                    failed_assignments.append((teacher, class_name, subject, remaining_hours, allocated_hours))
                else:
                    print(f"Warning: Could not parse line {line_num}: {line}")
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []
    
    return failed_assignments

def analyze_failed_assignments(failed_assignments: List[Tuple[str, str, str, int, int]]) -> None:
    """
    Analyze the failed assignments and print statistics.
    
    Args:
        failed_assignments: List of failed assignment tuples
    """
    if not failed_assignments:
        print("No failed assignments to analyze.")
        return
    
    print(f"\n=== FAILED ASSIGNMENTS ANALYSIS ===")
    print(f"Total failed assignments: {len(failed_assignments)}")
    
    # Count by teacher
    teacher_failures = {}
    for teacher, class_name, subject, remaining, allocated in failed_assignments:
        if teacher not in teacher_failures:
            teacher_failures[teacher] = []
        teacher_failures[teacher].append((class_name, subject, remaining, allocated))
    
    print(f"\nTeachers with failed assignments: {len(teacher_failures)}")
    print("\nTop 10 teachers with most failures:")
    sorted_teachers = sorted(teacher_failures.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (teacher, failures) in enumerate(sorted_teachers[:10]):
        total_remaining = sum(f[2] for f in failures)
        print(f"  {i+1}. {teacher}: {len(failures)} failures, {total_remaining} hours remaining")
    
    # Count by subject
    subject_failures = {}
    for teacher, class_name, subject, remaining, allocated in failed_assignments:
        if subject not in subject_failures:
            subject_failures[subject] = 0
        subject_failures[subject] += remaining
    
    print(f"\nFailures by subject:")
    sorted_subjects = sorted(subject_failures.items(), key=lambda x: x[1], reverse=True)
    for subject, total_remaining in sorted_subjects:
        print(f"  {subject}: {total_remaining} hours remaining")
    
    # Count by class
    class_failures = {}
    for teacher, class_name, subject, remaining, allocated in failed_assignments:
        if class_name not in class_failures:
            class_failures[class_name] = 0
        class_failures[class_name] += remaining
    
    print(f"\nTop 10 classes with most failed hours:")
    sorted_classes = sorted(class_failures.items(), key=lambda x: x[1], reverse=True)
    for i, (class_name, total_remaining) in enumerate(sorted_classes[:10]):
        print(f"  {i+1}. {class_name}: {total_remaining} hours remaining")
    
    # Count completely failed vs partially allocated
    completely_failed = [f for f in failed_assignments if f[4] == 0]  # allocated_hours == 0
    partially_allocated = [f for f in failed_assignments if f[4] > 0]  # allocated_hours > 0
    
    print(f"\nAllocation status:")
    print(f"  Completely failed (0 hours allocated): {len(completely_failed)}")
    print(f"  Partially allocated (some hours allocated): {len(partially_allocated)}")
    
    total_remaining_hours = sum(f[3] for f in failed_assignments)
    total_allocated_hours = sum(f[4] for f in failed_assignments)
    total_needed_hours = total_remaining_hours + total_allocated_hours
    
    print(f"\nHours summary:")
    print(f"  Total hours needed: {total_needed_hours}")
    print(f"  Total hours allocated: {total_allocated_hours}")
    print(f"  Total hours remaining: {total_remaining_hours}")
    print(f"  Success rate: {(total_allocated_hours / total_needed_hours * 100):.1f}%")

def save_failed_assignments_csv(failed_assignments: List[Tuple[str, str, str, int, int]], 
                               output_path: str = 'failed_assignments.csv') -> pd.DataFrame:
    """
    Save failed assignments to a CSV file for easier analysis.
    
    Args:
        failed_assignments: List of failed assignment tuples
        output_path: Path for the output CSV file
        
    Returns:
        DataFrame containing the failed assignments
    """
    import pandas as pd
    
    if not failed_assignments:
        print("No failed assignments to save.")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(failed_assignments, 
                     columns=['Teacher', 'Class', 'Subject', 'Remaining_Hours', 'Allocated_Hours'])
    
    # Add calculated columns
    df['Total_Hours_Needed'] = df['Remaining_Hours'] + df['Allocated_Hours']
    df['Success_Rate'] = (df['Allocated_Hours'] / df['Total_Hours_Needed'] * 100).round(1)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Failed assignments saved to: {output_path}")
    
    return df

# Example usage and testing
def main():
    """Test the parsing functions with the failed.txt file."""
    file_path = '/Users/juan/Projects/oraccio/failed.txt'
    
    print("Testing tuple parsing with ast.literal_eval...")
    failed_list = parse_failed_assignments(file_path)
    
    if failed_list:
        print(f"Successfully parsed {len(failed_list)} failed assignments.")
        print("\nFirst 5 entries:")
        for i, entry in enumerate(failed_list[:5]):
            print(f"  {i+1}. {entry}")
        
        # Analyze the failed assignments
        analyze_failed_assignments(failed_list)
        
        # Save to CSV
        save_failed_assignments_csv(failed_list, '/Users/juan/Projects/oraccio/failed_assignments.csv')
    else:
        print("No valid assignments found.")
    
    print(f"\n" + "="*50)
    print("Testing regex parsing...")
    failed_list_regex = parse_failed_assignments_regex(file_path)
    
    if failed_list_regex:
        print(f"Successfully parsed {len(failed_list_regex)} failed assignments with regex.")
        
        # Compare results
        if failed_list == failed_list_regex:
            print("Both parsing methods produced identical results!")
        else:
            print("Warning: Parsing methods produced different results.")
    
    return failed_list

if __name__ == "__main__":
    failed_assignments = main()