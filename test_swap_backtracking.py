from improved_scheduler import ImprovedSchoolScheduler
from parse_failed import parse_failed_assignments

def test_swap_backtracking():
    """Test the swap backtracking functionality with actual failed assignments."""
    
    print("Testing Swap Backtracking System")
    print("=" * 50)
    
    # Load the failed assignments
    failed_assignments = parse_failed_assignments('/Users/juan/Projects/oraccio/failed.txt')
    print(f"Loaded {len(failed_assignments)} failed assignments")
    
    # Initialize scheduler
    scheduler = ImprovedSchoolScheduler('/Users/juan/Projects/oraccio/data/conseil_docente_cleaned.csv')
    
    # Run initial scheduling
    print("\nRunning initial schedule creation...")
    success_rate, allocated, total = scheduler.create_schedule()
    
    print(f"\nInitial Results:")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Allocated Hours: {allocated}/{total}")
    
    # The swap backtracking should have already run as part of create_schedule()
    # But we can also test individual components
    
    print(f"\nTesting individual swap backtracking components...")
    
    # Test a few failed assignments manually
    test_assignments = failed_assignments[:5]  # Test first 5
    
    for teacher, class_name, subject, remaining, allocated in test_assignments:
        print(f"\nTesting: {teacher} - {class_name} ({subject})")
        
        # Test if simple swap can work
        available_before = len(scheduler.get_available_slots(teacher, class_name))
        print(f"  Available slots before swap: {available_before}")
        
        # Test slot availability checking
        potential_slots = 0
        for day in scheduler.days:
            for hour in scheduler.hours:
                if scheduler.would_slot_work_if_free(teacher, class_name, day, hour):
                    potential_slots += 1
        
        print(f"  Potential slots if free: {potential_slots}")
        
        if potential_slots > available_before:
            print(f"  --> Swap backtracking could potentially help (gap of {potential_slots - available_before} slots)")
        else:
            print(f"  --> No additional slots possible through swapping")
    
    return scheduler

def demonstrate_swap_strategies():
    """Demonstrate different swap strategies."""
    
    print("\nSwap Backtracking Strategies Implemented:")
    print("=" * 50)
    
    strategies = [
        ("Simple Swap Placement", """
        - Tries direct placement first
        - If no slots available, attempts recursive swapping
        - Limited depth to prevent infinite loops
        - Focuses on moving one assignment to free a slot
        """),
        
        ("Chain Swap Placement", """
        - More aggressive multi-assignment moving
        - Can move multiple assignments in sequence
        - Uses sophisticated chain building algorithms
        - Higher success rate but more computationally expensive
        """),
        
        ("Recursive Swap Search", """
        - Deep search through possible swap combinations
        - Tracks tried swaps to avoid infinite loops
        - Can find complex multi-step solutions
        - Respects all existing constraints during swapping
        """),
        
        ("Constraint-Aware Swapping", """
        - Checks if slots would work even if free
        - Respects hour 14 restrictions
        - Maintains teacher daily limits (5 hours)
        - Maintains class daily limits (6-7 hours depending on day)
        - Maintains teacher-class combination limits (max 2 per day)
        """)
    ]
    
    for strategy_name, description in strategies:
        print(f"\n{strategy_name}:")
        print(description)
    
    print(f"\nKey Features of the Implementation:")
    print(f"- Automatically runs after initial scheduling")
    print(f"- Processes failed assignments in order of difficulty")
    print(f"- Uses multiple strategies with increasing complexity")
    print(f"- Tracks and reports recovery success")
    print(f"- Updates final success rate and allocation counts")
    print(f"- Maintains all original scheduling constraints")

if __name__ == "__main__":
    demonstrate_swap_strategies()
    scheduler = test_swap_backtracking()