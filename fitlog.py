#!/usr/bin/env python3

import sqlite3
import os
import re
from datetime import datetime

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
            return ""

    def log_workout(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        workout_date = datetime.now().isoformat()
        cursor.execute('INSERT INTO workouts (date) VALUES (?)', (workout_date,))
        workout_id = cursor.lastrowid
        
        # Get existing exercises for autocomplete
        existing_exercises = self.get_existing_exercises()
        
        self.clear_screen()
        print("=" * 40)
        print("         LOG WORKOUT")
        print("=" * 40)
        print()
        
        while True:
            exercise_name = self.get_exercise_input(existing_exercises)
            
            if not exercise_name:
                break
            
            unit = 'kg' if 'kg' in exercise_name.lower() else 'lbs'
            clean_name = re.sub(r'[^a-zA-Z0-9\s\-]', '', exercise_name).lower().strip()
            cursor.execute('INSERT INTO exercises (workout_id, name, unit) VALUES (?, ?, ?)', 
                         (workout_id, clean_name, unit))
            exercise_id = cursor.lastrowid
            
            set_number = 1
            while True:
                set_input = input(f"Set Weight and Reps (Weight Reps) or empty for none: ").strip()
                
                if not set_input:
                    break
                
                try:
                    parts = set_input.split()
                    if len(parts) == 2:
                        weight = float(parts[0])
                        reps = int(parts[1])
                        
                        cursor.execute('INSERT INTO sets (exercise_id, weight, reps, set_order) VALUES (?, ?, ?, ?)',
                                     (exercise_id, weight, reps, set_number))
                        set_number += 1
                        print(f"  ✓ Set {set_number-1}: {weight} {unit} x {reps}")
                    else:
                        print("  Invalid format. Use: Weight Reps")
                except ValueError:
                    print("  Invalid format. Use: Weight Reps")
            
            print()
        
        conn.commit()
        conn.close()
        
        print("Workout logged successfully!")
        input("Press Enter to continue...")
    
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