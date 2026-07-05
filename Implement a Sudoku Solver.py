import copy
import random
import time
from typing import List, Tuple, Optional, Set
from collections import defaultdict

class SudokuSolver:
    """Advanced Sudoku solver with multiple techniques"""
    
    def __init__(self, grid: List[List[int]]):
        """
        Initialize the solver with a grid
        
        Args:
            grid: 9x9 list of lists, 0 represents empty cells
        """
        self.original_grid = copy.deepcopy(grid)
        self.grid = grid
        self.size = 9
        self.box_size = 3
        self.solution_count = 0
        self.steps = 0
        self.techniques_used = {
            'naked_single': 0,
            'hidden_single': 0,
            'naked_pair': 0,
            'hidden_pair': 0,
            'pointing_pairs': 0,
            'box_line_reduction': 0,
            'backtracking': 0
        }
        self.candidates = None
        self.solve_time = 0
    
    def is_valid(self, grid: List[List[int]], row: int, col: int, num: int) -> bool:
        """Check if placing num at (row, col) is valid"""
        # Check row
        for c in range(self.size):
            if grid[row][c] == num:
                return False
        
        # Check column
        for r in range(self.size):
            if grid[r][col] == num:
                return False
        
        # Check 3x3 box
        box_row = (row // self.box_size) * self.box_size
        box_col = (col // self.box_size) * self.box_size
        for r in range(box_row, box_row + self.box_size):
            for c in range(box_col, box_col + self.box_size):
                if grid[r][c] == num:
                    return False
        
        return True
    
    def find_empty(self, grid: List[List[int]]) -> Optional[Tuple[int, int]]:
        """Find the next empty cell (with minimum candidates for efficiency)"""
        min_candidates = 10
        best_cell = None
        
        for row in range(self.size):
            for col in range(self.size):
                if grid[row][col] == 0:
                    # Count candidates
                    candidates = self.get_candidates(grid, row, col)
                    if len(candidates) < min_candidates:
                        min_candidates = len(candidates)
                        best_cell = (row, col)
                        if min_candidates == 1:  # Early exit if single candidate
                            return best_cell
        
        return best_cell
    
    def get_candidates(self, grid: List[List[int]], row: int, col: int) -> Set[int]:
        """Get all possible candidates for a cell"""
        if grid[row][col] != 0:
            return set()
        
        candidates = set(range(1, 10))
        
        # Remove numbers in row
        for c in range(self.size):
            if grid[row][c] in candidates:
                candidates.remove(grid[row][c])
        
        # Remove numbers in column
        for r in range(self.size):
            if grid[r][col] in candidates:
                candidates.remove(grid[r][col])
        
        # Remove numbers in box
        box_row = (row // self.box_size) * self.box_size
        box_col = (col // self.box_size) * self.box_size
        for r in range(box_row, box_row + self.box_size):
            for c in range(box_col, box_col + self.box_size):
                if grid[r][c] in candidates:
                    candidates.remove(grid[r][c])
        
        return candidates
    
    def update_candidates(self, grid: List[List[int]]) -> List[List[Set[int]]]:
        """Update candidates for all empty cells"""
        candidates = [[set() for _ in range(self.size)] for _ in range(self.size)]
        for row in range(self.size):
            for col in range(self.size):
                if grid[row][col] == 0:
                    candidates[row][col] = self.get_candidates(grid, row, col)
        return candidates
    
    def solve_logical(self) -> bool:
        """Apply logical solving techniques before backtracking"""
        progress = True
        iterations = 0
        
        while progress and iterations < 100:
            progress = False
            iterations += 1
            self.candidates = self.update_candidates(self.grid)
            
            # 1. Naked Single - only one candidate
            for row in range(self.size):
                for col in range(self.size):
                    if self.grid[row][col] == 0 and len(self.candidates[row][col]) == 1:
                        num = next(iter(self.candidates[row][col]))
                        self.grid[row][col] = num
                        self.techniques_used['naked_single'] += 1
                        self.steps += 1
                        progress = True
            
            # 2. Hidden Single - only one cell in row/col/box can contain a number
            for num in range(1, 10):
                # Check rows
                for row in range(self.size):
                    possible_cols = []
                    for col in range(self.size):
                        if self.grid[row][col] == 0 and num in self.candidates[row][col]:
                            possible_cols.append(col)
                    if len(possible_cols) == 1:
                        self.grid[row][possible_cols[0]] = num
                        self.techniques_used['hidden_single'] += 1
                        self.steps += 1
                        progress = True
                
                # Check columns
                for col in range(self.size):
                    possible_rows = []
                    for row in range(self.size):
                        if self.grid[row][col] == 0 and num in self.candidates[row][col]:
                            possible_rows.append(row)
                    if len(possible_rows) == 1:
                        self.grid[possible_rows[0]][col] = num
                        self.techniques_used['hidden_single'] += 1
                        self.steps += 1
                        progress = True
                
                # Check boxes
                for box_row in range(0, self.size, self.box_size):
                    for box_col in range(0, self.size, self.box_size):
                        possible_cells = []
                        for r in range(box_row, box_row + self.box_size):
                            for c in range(box_col, box_col + self.box_size):
                                if self.grid[r][c] == 0 and num in self.candidates[r][c]:
                                    possible_cells.append((r, c))
                        if len(possible_cells) == 1:
                            r, c = possible_cells[0]
                            self.grid[r][c] = num
                            self.techniques_used['hidden_single'] += 1
                            self.steps += 1
                            progress = True
            
            # 3. Naked Pair - two cells in same unit with same two candidates
            for row in range(self.size):
                for col in range(self.size):
                    if self.grid[row][col] == 0 and len(self.candidates[row][col]) == 2:
                        pair = self.candidates[row][col]
                        # Check row
                        for c2 in range(col + 1, self.size):
                            if (self.grid[row][c2] == 0 and 
                                self.candidates[row][c2] == pair):
                                # Remove these candidates from other cells in row
                                for c3 in range(self.size):
                                    if c3 != col and c3 != c2 and self.grid[row][c3] == 0:
                                        if pair.issubset(self.candidates[row][c3]):
                                            self.candidates[row][c3] -= pair
                                            self.techniques_used['naked_pair'] += 1
                                            progress = True
            
            # If all cells are filled, we're done
            if all(self.grid[row][col] != 0 for row in range(self.size) for col in range(self.size)):
                return True
        
        return False
    
    def solve_backtracking(self, grid: List[List[int]]) -> bool:
        """Solve using backtracking with MRV heuristic"""
        self.steps += 1
        self.techniques_used['backtracking'] += 1
        
        empty = self.find_empty(grid)
        if not empty:
            return True  # Solved
        
        row, col = empty
        candidates = self.get_candidates(grid, row, col)
        
        for num in sorted(candidates):
            if self.is_valid(grid, row, col, num):
                grid[row][col] = num
                
                if self.solve_backtracking(grid):
                    return True
                
                grid[row][col] = 0  # Backtrack
        
        return False
    
    def solve(self, use_logical: bool = True) -> bool:
        """
        Solve the puzzle using a combination of logical and backtracking techniques
        
        Args:
            use_logical: If True, apply logical techniques first
        """
        start_time = time.time()
        self.steps = 0
        
        # Try logical solving first
        if use_logical:
            if self.solve_logical():
                self.solve_time = time.time() - start_time
                return True
        
        # If logical solving didn't complete, use backtracking
        print("🧠 Applying backtracking to solve remaining cells...")
        result = self.solve_backtracking(self.grid)
        
        self.solve_time = time.time() - start_time
        return result
    
    def count_solutions(self, grid: List[List[int]], limit: int = 2) -> int:
        """Count number of solutions (useful for checking uniqueness)"""
        empty = self.find_empty(grid)
        if not empty:
            return 1
        
        row, col = empty
        count = 0
        
        for num in range(1, 10):
            if self.is_valid(grid, row, col, num):
                grid[row][col] = num
                count += self.count_solutions(grid, limit)
                grid[row][col] = 0
                
                if count >= limit:
                    return count
        
        return count
    
    def is_valid_puzzle(self) -> bool:
        """Check if the puzzle is valid (no contradictions)"""
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] != 0:
                    num = self.grid[row][col]
                    self.grid[row][col] = 0
                    if not self.is_valid(self.grid, row, col, num):
                        self.grid[row][col] = num
                        return False
                    self.grid[row][col] = num
        return True
    
    def get_difficulty_rating(self) -> str:
        """Estimate puzzle difficulty based on solution techniques used"""
        total = sum(self.techniques_used.values())
        if total == 0:
            return "Unknown"
        
        # Weight techniques by difficulty
        score = (
            self.techniques_used['naked_single'] * 1 +
            self.techniques_used['hidden_single'] * 2 +
            self.techniques_used['naked_pair'] * 3 +
            self.techniques_used['hidden_pair'] * 4 +
            self.techniques_used['pointing_pairs'] * 5 +
            self.techniques_used['box_line_reduction'] * 6 +
            self.techniques_used['backtracking'] * 10
        )
        
        if score < 20:
            return "Very Easy"
        elif score < 50:
            return "Easy"
        elif score < 100:
            return "Medium"
        elif score < 200:
            return "Hard"
        else:
            return "Very Hard"
    
    def print_grid(self, grid: Optional[List[List[int]]] = None, 
                   show_candidates: bool = False) -> None:
        """Pretty print the Sudoku grid"""
        if grid is None:
            grid = self.grid
        
        print("\n" + "="*37)
        for row in range(self.size):
            if row % self.box_size == 0 and row != 0:
                print("="*37)
            
            for col in range(self.size):
                if col % self.box_size == 0:
                    print("||", end=" ")
                
                val = grid[row][col]
                if val == 0:
                    print("·", end=" ")
                else:
                    print(val, end=" ")
                
                if col == self.size - 1:
                    print("||")
        print("="*37)
        
        if show_candidates and self.candidates:
            print("\nCandidates:")
            for row in range(self.size):
                for col in range(self.size):
                    if grid[row][col] == 0 and self.candidates[row][col]:
                        print(f"({row},{col}): {sorted(self.candidates[row][col])}")
    
    def get_solution_stats(self) -> dict:
        """Get statistics about the solution process"""
        total = sum(self.techniques_used.values())
        return {
            'steps': self.steps,
            'solve_time': self.solve_time,
            'techniques_used': self.techniques_used,
            'total_techniques': total,
            'difficulty': self.get_difficulty_rating()
        }

class SudokuGenerator:
    """Generate Sudoku puzzles with varying difficulty"""
    
    @staticmethod
    def generate_solution() -> List[List[int]]:
        """Generate a complete valid Sudoku solution"""
        grid = [[0] * 9 for _ in range(9)]
        solver = SudokuSolver(grid)
        
        # Fill diagonal boxes first
        for box in range(0, 9, 3):
            numbers = list(range(1, 10))
            random.shuffle(numbers)
            for r in range(box, box + 3):
                for c in range(box, box + 3):
                    grid[r][c] = numbers.pop()
        
        # Solve the rest
        solver.solve_backtracking(grid)
        return grid
    
    @staticmethod
    def generate_puzzle(difficulty: str = 'medium') -> Tuple[List[List[int]], List[List[int]]]:
        """
        Generate a Sudoku puzzle by removing numbers from a solution
        
        Args:
            difficulty: 'easy', 'medium', 'hard', 'expert'
        
        Returns:
            Tuple of (puzzle_grid, solution_grid)
        """
        solution = SudokuGenerator.generate_solution()
        puzzle = copy.deepcopy(solution)
        
        # Number of cells to remove based on difficulty
        remove_counts = {
            'easy': 30,
            'medium': 45,
            'hard': 55,
            'expert': 65
        }
        
        count = remove_counts.get(difficulty, 40)
        positions = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(positions)
        
        removed = 0
        for r, c in positions:
            if removed >= count:
                break
            
            # Try removing this cell
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            
            # Check if puzzle still has unique solution
            solver = SudokuSolver(copy.deepcopy(puzzle))
            solutions = solver.count_solutions(copy.deepcopy(puzzle), limit=2)
            
            if solutions == 1:
                removed += 1
            else:
                puzzle[r][c] = backup
        
        return puzzle, solution

class SudokuUI:
    """User interface for Sudoku solver"""
    
    @staticmethod
    def display_welcome():
        """Display welcome message"""
        print("\n" + "="*60)
        print("🧩 SUDOKU SOLVER & GENERATOR 🧩")
        print("="*60)
        print("This program can:")
        print("  1. Solve Sudoku puzzles")
        print("  2. Generate new puzzles")
        print("  3. Analyze puzzles")
        print("  4. Step through solutions")
        print("="*60)
    
    @staticmethod
    def parse_grid_input() -> List[List[int]]:
        """Parse user input into a 9x9 grid"""
        print("\nEnter Sudoku puzzle (use 0 or . for empty cells)")
        print("Option 1: Enter 9 rows of 9 digits each")
        print("Option 2: Enter a single string of 81 digits")
        print("Example: 530070000600195000098000060800060003400803001700020006060000280000419005000080079")
        print()
        
        grid = []
        while True:
            choice = input("Enter 'r' for rows or 's' for single string: ").lower()
            
            if choice == 'r':
                print("Enter 9 rows, each with 9 digits (0 for empty):")
                for i in range(9):
                    while True:
                        row = input(f"Row {i+1}: ").strip()
                        if len(row) == 9 and all(c.isdigit() for c in row):
                            grid.append([int(c) for c in row])
                            break
                        else:
                            print("Invalid row. Please enter exactly 9 digits.")
                break
            
            elif choice == 's':
                while True:
                    text = input("Enter 81 digits: ").strip()
                    if len(text) == 81 and all(c.isdigit() for c in text):
                        grid = [[int(text[i*9 + j]) for j in range(9)] for i in range(9)]
                        break
                    else:
                        print("Invalid input. Please enter exactly 81 digits.")
                break
            else:
                print("Invalid choice. Please enter 'r' or 's'.")
        
        return grid
    
    @staticmethod
    def display_example_puzzle():
        """Display an example puzzle"""
        example = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9]
        ]
        return example
    
    def solve_menu(self):
        """Menu for solving puzzles"""
        print("\n" + "-"*60)
        print("🔧 SOLVE PUZZLE")
        print("-"*60)
        print("1. Enter custom puzzle")
        print("2. Use example puzzle")
        print("3. Generate random puzzle")
        print("4. Back to main menu")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            grid = self.parse_grid_input()
        elif choice == '2':
            grid = self.display_example_puzzle()
        elif choice == '3':
            difficulty = self.select_difficulty()
            grid, solution = SudokuGenerator.generate_puzzle(difficulty)
        else:
            return
        
        self.solve_puzzle(grid)
    
    def solve_puzzle(self, grid: List[List[int]]):
        """Solve and display the puzzle"""
        print("\n📋 Original Puzzle:")
        solver = SudokuSolver(grid)
        solver.print_grid()
        
        # Check if puzzle is valid
        if not solver.is_valid_puzzle():
            print("❌ Invalid puzzle! Contains contradictions.")
            return
        
        # Check for uniqueness
        print("\n🔍 Checking puzzle validity...")
        temp_grid = copy.deepcopy(grid)
        temp_solver = SudokuSolver(temp_grid)
        solutions = temp_solver.count_solutions(temp_grid, limit=2)
        
        if solutions == 0:
            print("❌ Puzzle has no solutions!")
            return
        elif solutions == 1:
            print("✅ Puzzle has a unique solution.")
        else:
            print(f"⚠️  Puzzle has {solutions} solutions (not unique).")
            return
        
        # Solve
        print("\n🧠 Solving...")
        success = solver.solve(use_logical=True)
        
        if success:
            print("\n✅ Solution Found!")
            print("\n📋 Solution Grid:")
            solver.print_grid()
            
            # Display statistics
            stats = solver.get_solution_stats()
            print("\n📊 Solution Statistics:")
            print(f"   Steps: {stats['steps']}")
            print(f"   Time: {stats['solve_time']:.3f} seconds")
            print(f"   Difficulty: {stats['difficulty']}")
            print("\n   Techniques Used:")
            for technique, count in stats['techniques_used'].items():
                if count > 0:
                    print(f"     - {technique.replace('_', ' ').title()}: {count}")
        else:
            print("❌ Could not solve the puzzle!")
    
    def select_difficulty(self) -> str:
        """Select difficulty level"""
        print("\nSelect difficulty:")
        print("1. Easy")
        print("2. Medium")
        print("3. Hard")
        print("4. Expert")
        
        choice = input("Enter choice (1-4): ").strip()
        difficulties = ['', 'easy', 'medium', 'hard', 'expert']
        
        try:
            return difficulties[int(choice)]
        except:
            print("Invalid choice. Using Medium.")
            return 'medium'
    
    def analyze_menu(self):
        """Analyze a puzzle"""
        print("\n" + "-"*60)
        print("📊 ANALYZE PUZZLE")
        print("-"*60)
        
        grid = self.parse_grid_input()
        solver = SudokuSolver(grid)
        
        # Check validity
        print("\n🔍 Analyzing puzzle...")
        if not solver.is_valid_puzzle():
            print("❌ Invalid puzzle! Contains contradictions.")
            return
        
        # Count solutions
        temp_grid = copy.deepcopy(grid)
        solutions = solver.count_solutions(temp_grid, limit=3)
        
        if solutions == 0:
            print("❌ No solutions exist!")
        elif solutions == 1:
            print("✅ Unique solution!")
        else:
            print(f"⚠️  {solutions} solutions found (puzzle is not unique)")
        
        # Count empty cells
        empty_count = sum(1 for r in range(9) for c in range(9) if grid[r][c] == 0)
        print(f"📊 Empty cells: {empty_count}/81 ({empty_count/81*100:.1f}%)")
        
        # Try to solve and get difficulty
        solver.solve(use_logical=True)
        stats = solver.get_solution_stats()
        print(f"📊 Estimated difficulty: {stats['difficulty']}")
    
    def run(self):
        """Main UI loop"""
        self.display_welcome()
        
        while True:
            print("\n" + "="*60)
            print("MAIN MENU")
            print("="*60)
            print("1. 🔧 Solve a puzzle")
            print("2. 🎲 Generate a puzzle")
            print("3. 📊 Analyze a puzzle")
            print("4. ❌ Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                self.solve_menu()
            elif choice == '2':
                difficulty = self.select_difficulty()
                puzzle, solution = SudokuGenerator.generate_puzzle(difficulty)
                print(f"\n🎲 Generated {difficulty} puzzle:")
                
                solver = SudokuSolver(puzzle)
                solver.print_grid()
                
                input("\nPress Enter to solve...")
                
                solver.solve(use_logical=True)
                print("\n✅ Solved:")
                solver.print_grid()
                
                stats = solver.get_solution_stats()
                print(f"\n📊 Difficulty: {stats['difficulty']}")
                print(f"   Steps: {stats['steps']}")
                print(f"   Time: {stats['solve_time']:.3f}s")
            
            elif choice == '3':
                self.analyze_menu()
            
            elif choice == '4':
                print("\n👋 Thank you for using the Sudoku Solver! Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-4.")
            
            input("\nPress Enter to continue...")

def main():
    """Main entry point"""
    try:
        ui = SudokuUI()
        ui.run()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()