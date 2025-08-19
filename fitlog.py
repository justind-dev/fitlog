#!/usr/bin/env python3

import sqlite3
import os
import re
from datetime import datetime

# Available units for exercises
EXERCISE_UNITS = ['lbs', 'kg', 'minutes', 'reps', 'miles', 'km', 'seconds', 'hours']

class FitLog:
    def __init__(self):
        self.db_path = 'fitlog.db'
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER,
                name TEXT NOT NULL,
                unit TEXT DEFAULT 'lbs',
                FOREIGN KEY (workout_id) REFERENCES workouts (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id INTEGER,
                weight REAL,
                reps INTEGER,
                set_order INTEGER,
                FOREIGN KEY (exercise_id) REFERENCES exercises (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_existing_exercises(self):
        """
        Retrieve all unique exercise names from the database for autocomplete.
        Returns a list of exercise names sorted alphabetically.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT DISTINCT name FROM exercises ORDER BY name')
            exercises = [row[0] for row in cursor.fetchall()]
            return exercises
        except sqlite3.Error as e:
            print(f"Database error retrieving exercises: {e}")
            return []
        finally:
            conn.close()
    
    def get_exercise_with_unit(self, exercise_name):
        """
        Retrieve exercise unit from database if exercise exists.
        Returns the unit if found, None if exercise doesn't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT unit FROM exercises WHERE name = ? LIMIT 1', (exercise_name,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error retrieving exercise unit: {e}")
            return None
        finally:
            conn.close()
    
    def get_exercise_input(self, existing_exercises):
        """
        Get exercise name input with autocomplete fallback to basic input.
        """
        try:
            from prompt_toolkit import prompt
            from prompt_toolkit.completion import WordCompleter
            
            exercise_completer = WordCompleter(existing_exercises, ignore_case=True)
            exercise_name = prompt("Exercise Name (or empty to quit logging): ", 
                                 completer=exercise_completer).strip()
            return exercise_name
        except ImportError:
            # Fallback to basic input if prompt-toolkit not available
            return input("Exercise Name (or empty to quit logging): ").strip()
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            return None
    
    def get_exercise_unit(self):
        """
        Get unit input with autocomplete from predefined units.
        Returns the selected unit string, or None if cancelled.
        """
        while True:
            try:
                from prompt_toolkit import prompt
                from prompt_toolkit.completion import WordCompleter
                
                unit_completer = WordCompleter(EXERCISE_UNITS, ignore_case=True)
                unit = prompt("Unit for this exercise: ", completer=unit_completer).strip()
                
                if not unit:
                    return 'reps'  # Default to 'reps' if empty
                elif unit.lower() in [u.lower() for u in EXERCISE_UNITS]:
                    return unit.lower()
                else:
                    print(f"Invalid unit. Please choose from: {', '.join(EXERCISE_UNITS)}")
                    continue
                    
            except ImportError:
                # Fallback to basic input if prompt-toolkit not available
                print(f"Available units: {', '.join(EXERCISE_UNITS)}")
                try:
                    unit = input("Unit for this exercise: ").strip()
                    
                    if not unit:
                        return 'reps'  # Default to 'reps' if empty
                    elif unit.lower() in [u.lower() for u in EXERCISE_UNITS]:
                        return unit.lower()
                    else:
                        print(f"Invalid unit. Please choose from: {', '.join(EXERCISE_UNITS)}")
                        continue
                        
                except KeyboardInterrupt:
                    print("\nCancelled, returning to exercise input...")
                    return None
            except KeyboardInterrupt:
                print("\nCancelled, returning to exercise input...")
                return None

    def get_set_input(self, unit, set_number):
        """
        Get set input with proper prompting based on unit type.
        Returns tuple (value, reps) or None if cancelled/empty.
        """
        try:
            # Customize prompt based on unit type
            if unit in ['miles', 'km']:
                prompt_text = f"Set Distance (e.g., '3.5' for 3.5 {unit}) or empty for none: "
            elif unit in ['minutes', 'seconds', 'hours']:
                prompt_text = f"Set Duration (e.g., '30' for 30 {unit}) or empty for none: "
            elif unit == 'reps':
                prompt_text = f"Set Reps (e.g., '15') or empty for none: "
            else:
                prompt_text = f"Set Weight and Reps (Weight Reps) or empty for none: "
            
            set_input = input(prompt_text).strip()
            
            if not set_input:
                return None
            
            # Parse input based on unit type
            if unit in ['minutes', 'seconds', 'hours', 'miles', 'km'] or unit == 'reps':
                # Single value exercises
                value = float(set_input)
                return (value, 1)
            else:
                # Weight-based exercises need weight and reps
                parts = set_input.split()
                if len(parts) == 2:
                    weight = float(parts[0])
                    reps = int(parts[1])
                    return (weight, reps)
                else:
                    print("  Invalid format. Use: Weight Reps")
                    return self.get_set_input(unit, set_number)  # Retry
                    
        except ValueError:
            if unit in ['minutes', 'seconds', 'hours', 'miles', 'km'] or unit == 'reps':
                print(f"  Invalid format. Enter a number for {unit}")
            else:
                print("  Invalid format. Use: Weight Reps")
            return self.get_set_input(unit, set_number)  # Retry
        except KeyboardInterrupt:
            return "CANCELLED"  # Special return value to indicate cancellation

    def display_workout_confirmation(self, workout_data):
        """
        Display workout confirmation table and get user approval.
        Returns True if confirmed, False if cancelled.
        """
        print("\n" + "=" * 50)
        print("         WORKOUT CONFIRMATION")
        print("=" * 50)
        
        for exercise_data in workout_data:
            exercise_name = exercise_data['name']
            unit = exercise_data['unit']
            sets = exercise_data['sets']
            is_new = exercise_data['is_new']
            
            # Display exercise header
            new_indicator = " (new)" if is_new else ""
            print(f"\n{exercise_name.title()} ({unit}){new_indicator}")
            print("-" * (len(exercise_name) + len(unit) + len(new_indicator) + 3))
            
            # Display sets
            for i, (weight, reps) in enumerate(sets, 1):
                if unit in ['minutes', 'seconds', 'hours', 'miles', 'km'] or unit == 'reps':
                    print(f"  Set {i}: {weight} {unit}")
                else:
                    print(f"  Set {i}: {weight} {unit} x {reps}")
        
        print("\n" + "=" * 50)
        
        try:
            confirm = input("Confirm and save workout? (y/n): ").strip().lower()
            return confirm == 'y'
        except KeyboardInterrupt:
            print("\nWorkout cancelled.")
            return False

    def save_workout_to_db(self, workout_data):
        """
        Save the workout data to database in a single transaction.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create workout record
            workout_date = datetime.now().isoformat()
            cursor.execute('INSERT INTO workouts (date) VALUES (?)', (workout_date,))
            workout_id = cursor.lastrowid
            
            # Save exercises and sets
            for exercise_data in workout_data:
                # Create exercise record
                cursor.execute('INSERT INTO exercises (workout_id, name, unit) VALUES (?, ?, ?)', 
                             (workout_id, exercise_data['name'], exercise_data['unit']))
                exercise_id = cursor.lastrowid
                
                # Create set records
                for set_order, (weight, reps) in enumerate(exercise_data['sets'], 1):
                    cursor.execute('INSERT INTO sets (exercise_id, weight, reps, set_order) VALUES (?, ?, ?, ?)',
                                 (exercise_id, weight, reps, set_order))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error saving workout: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def main_menu(self):
        while True:
            self.clear_screen()
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⢤⡖⠺⠉⠓⠢⣄⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⢞⣿⣿⣭⣟⣯⣾⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⢸⣅⠉⠀⢻⣦⠀⡀⠘⣆⠀⠀⠀⠀⠀⠀")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣟⣿⡿⣿⣿⣿⢟⣿⣿⠟⢿⡀⠀⠀⠀⠀⠀⠀⠀⢟⣿⣾⣿⣿⣿⣇⠀⢡⠘⣆⠀⠀⠀⠀⠀")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣶⣿⣻⡿⠁⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠉⠉⠁⢻⠈⡆⢳⡈⢳⡀⠀⠀⠀")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⢿⣿⣿⣿⣿⣽⣿⡏⠀⠐⠾⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠟⢰⡥⠀⢝⣄⠀⠀")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣷⡘⠃⠀⠀⠀⠀⠙⢁⣱⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⢣⠞⣀⢇⠈⠱⠚⣆⠀")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⢿⣻⣿⣿⣿⡅⠀⠀⠀⢦⣬⡇⠀⠀⠀⠀⠀⠀⠀⢠⠚⡏⠉⠑⢺⡄⠀⠀⠙⣧⡀⠇⠀⡇")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⣷⠈⠉⠙⠛⠿⢿⣷⣦⣄⢰⣾⠖⣊⣉⡩⠍⢉⠓⠶⣿⢁⠜⢇⠁⢀⣹⣷⣤⣤⣈⣇⠀⣸⢧")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⢛⡇⠉⠀⠀⡀⢀⡀⠀⠀⠉⢙⡏⠁⠀⢹⣇⡀⠙⣏⠢⡌⡉⠉⣒⡷⠚⠉⠉⢻⣿⣿⣿⣵⣾⣷⣾")
            print("⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠚⠁⢀⣼⠋⣿⡅⠀⠀⠀⠀⠈⠉⠓⣦⡨⠀⡀⠀⠀⢈⣉⡒⠒⣶⡶⠂⠉⠀⠠⣤⣴⣶⣾⣿⣿⠿⠛⠉⠁")
            print("⠀⠀⠀⠀⠀⠀⠀⣴⠋⠉⠙⠋⠉⢸⣥⡤⠜⠋⢤⣦⢤⣤⣴⡾⠟⠁⠀⠙⢒⣫⣥⣴⣶⣿⣏⠀⠉⠛⠿⢿⣿⣿⣿⡿⠋⠁⠀⠀⠀⠀")
            print("⠀⠀⠀⠀⢀⡤⠚⠙⣷⣿⣦⡀⠀⢨⡏⠀⠀⠀⠀⠀⠀⠀⣩⠀⠀⠀⠉⠉⠉⢉⡛⢻⣿⣿⣿⣷⣶⣶⣶⣶⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⠀⠀⣰⠏⢀⠀⠀⣖⠈⠁⠉⠙⢻⣷⣄⣀⣤⣤⡴⠿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⣿⣿⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⠀⠀⡏⢰⡟⠀⠀⣿⡄⠀⠀⠀⣿⠀⠀⠀⠀⠀⢀⣴⠟⠁⢿⣄⣀⡀⠀⣀⣤⣶⣿⣿⣾⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⠀⣸⠀⢸⡁⠀⠀⠸⣿⣄⠀⡀⣿⠀⠀⡠⣶⡷⠋⡀⠀⠀⠚⠛⠛⠛⠛⠛⠛⠃⠈⠑⡿⢸⣯⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⢠⠇⠀⠘⣿⣦⣤⣤⣿⡟⠛⠓⢿⣞⠻⠟⣔⠲⡇⣀⡀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠀⢠⣾⣺⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⢸⠀⠀⠀⣿⣿⠉⠛⠿⢦⣄⡠⠘⡆⣀⣤⠀⠀⠀⢐⣮⠗⠃⠋⠛⠛⠛⠛⠛⢻⣿⡿⡍⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⣼⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠭⠌⣧⢾⣧⣤⣾⣦⠥⢠⣀⣀⢄⣠⣦⣶⣾⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⣿⠀⣀⣴⣿⣿⣿⣿⣦⡂⠀⠀⠀⣾⣙⡇⠀⠀⠀⠀⠀⠀⠁⠀⣡⣿⣿⣿⣿⣯⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⣿⡿⢋⣡⣾⣿⣿⣟⣻⠿⣿⠷⣤⣿⣿⣇⠀⠀⠀⠀⠀⠠⣀⣿⣿⣿⠛⠛⠻⠏⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⢰⡟⣻⣿⣿⣿⣿⣿⣼⡏⠀⠈⠑⢤⣹⡿⣿⣯⠻⢿⣿⣿⣿⣽⠿⢟⣃⣀⣀⡨⣏⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⣾⣾⠁⠀⠈⢹⣿⣿⠟⠀⠀⠀⠀⠀⠈⠛⢾⣿⡆⣶⣿⣿⠗⠒⢉⣉⣉⣙⣛⢿⣧⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⢹⣿⠀⠀⢷⡀⢻⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣷⣿⣿⣷⣿⣿⣿⣿⣿⣟⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠈⠿⣄⠀⣸⣿⣄⣻⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣏⣉⣉⣉⣉⣉⣿⣏⣉⣉⣉⣉⣉⣉⣙⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print("⠀⠀⠀⠙⢷⣌⠧⠈⡇⠀⠀⠀⠀⠀⠀⠀⠀⢠⡟⣟⣏⣿⣷⡇⢸⣿⣿⣿⣿⣿⠆⣿⠀⠿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
            print()
            print("███████╗██╗████████╗    ██╗      ██████╗  ██████╗ ")
            print("██╔════╝██║╚══██╔══╝    ██║     ██╔═══██╗██╔════╝ ")
            print("█████╗  ██║   ██║       ██║     ██║   ██║██║  ███╗")
            print("██╔══╝  ██║   ██║       ██║     ██║   ██║██║   ██║")
            print("██║     ██║   ██║       ███████╗╚██████╔╝╚██████╔╝")
            print("╚═╝     ╚═╝   ╚═╝       ╚══════╝ ╚═════╝  ╚═════╝ ")
            print()
            print("=" * 60)
            print("1. Log workout")
            print("2. Analysis")
            print("3. Exit")
            print()
            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                self.log_workout()
            elif choice == '2':
                self.analysis()
            elif choice == '3':
                print("\nGoodbye!")
                break
            else:
                input("Invalid option. Press Enter to continue...")

    def log_workout(self):
        try:
            # Get existing exercises for autocomplete and new exercise detection
            existing_exercises = self.get_existing_exercises()
            
            self.clear_screen()
            print("=" * 40)
            print("         LOG WORKOUT")
            print("=" * 40)
            print()
            
            workout_data = []  # Store all workout data in memory
            
            while True:
                exercise_name = self.get_exercise_input(existing_exercises)
                
                if exercise_name is None:  # Cancelled via Ctrl+C
                    break
                if not exercise_name:  # Empty input to quit
                    break
                
                clean_name = re.sub(r'[^a-zA-Z0-9\s\-]', '', exercise_name).lower().strip()
                
                # Check if exercise exists and get its unit, or prompt for new unit
                existing_unit = self.get_exercise_with_unit(clean_name)
                if existing_unit:
                    unit = existing_unit
                    is_new_exercise = False
                    print(f"Using existing exercise: {clean_name} ({unit})")
                else:
                    unit = self.get_exercise_unit()
                    if unit is None:  # Cancelled via Ctrl+C
                        continue  # Back to exercise name input
                    is_new_exercise = True
                    print(f"New exercise: {clean_name} ({unit})")
                    # Add to existing exercises list for future autocomplete in this session
                    existing_exercises.append(clean_name)
                    existing_exercises.sort()
                
                # Set input loop with cancellation handling
                sets_entered = []
                set_number = 1
                
                while True:
                    set_result = self.get_set_input(unit, set_number)
                    
                    if set_result == "CANCELLED":
                        # Handle cancellation based on whether sets were entered
                        if sets_entered:
                            try:
                                confirm = input(f"\nYou have entered {len(sets_entered)} set(s). Discard and return to exercise input? (y/n): ").strip().lower()
                                if confirm == 'y':
                                    print("Sets discarded, returning to exercise input...")
                                    break  # Exit set loop, back to exercise input
                                else:
                                    continue  # Stay in set input loop
                            except KeyboardInterrupt:
                                print("\nReturning to exercise input...")
                                break
                        else:
                            print("\nCancelled, returning to exercise input...")
                            break  # Exit set loop, back to exercise input
                    elif set_result is None:
                        # Empty input, done with sets
                        break
                    else:
                        # Valid set entered
                        weight, reps = set_result
                        sets_entered.append((weight, reps))
                        
                        # Show confirmation based on unit type
                        if unit in ['minutes', 'seconds', 'hours', 'miles', 'km'] or unit == 'reps':
                            print(f"  ✓ Set {set_number}: {weight} {unit}")
                        else:
                            print(f"  ✓ Set {set_number}: {weight} {unit} x {reps}")
                        
                        set_number += 1
                
                # If sets were entered, add exercise to workout data
                if sets_entered:
                    workout_data.append({
                        'name': clean_name,
                        'unit': unit,
                        'sets': sets_entered,
                        'is_new': is_new_exercise
                    })
                
                print()  # Blank line between exercises
            
            # If no exercises were logged, just return
            if not workout_data:
                print("No exercises logged.")
                input("Press Enter to continue...")
                return
            
            # Display confirmation table and save if approved
            if self.display_workout_confirmation(workout_data):
                if self.save_workout_to_db(workout_data):
                    print("\nWorkout logged successfully!")
                else:
                    print("\nError saving workout. Please try again.")
            else:
                print("\nWorkout cancelled.")
            
            input("Press Enter to continue...")
            
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            return
    
    def analysis(self):
        self.clear_screen()
        print("=" * 40)
        print("         ANALYSIS")
        print("=" * 40)
        print()
        print("Coming soon...")
        print()
        input("Press Enter to continue...")

def main():
    app = FitLog()
    app.main_menu()

if __name__ == "__main__":
    main()