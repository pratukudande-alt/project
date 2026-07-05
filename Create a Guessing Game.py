import random
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class GuessGame:
    """A number guessing game with multiple difficulty levels and statistics"""
    
    DIFFICULTIES = {
        'easy': {
            'range': (1, 50),
            'max_attempts': 10,
            'hints': True,
            'description': '1-50, 10 attempts, hints available'
        },
        'medium': {
            'range': (1, 100),
            'max_attempts': 7,
            'hints': True,
            'description': '1-100, 7 attempts, hints available'
        },
        'hard': {
            'range': (1, 200),
            'max_attempts': 5,
            'hints': False,
            'description': '1-200, 5 attempts, no hints'
        },
        'expert': {
            'range': (1, 500),
            'max_attempts': 4,
            'hints': False,
            'description': '1-500, 4 attempts, no hints'
        }
    }
    
    def __init__(self, stats_file='guess_game_stats.json'):
        self.stats_file = stats_file
        self.stats = self.load_stats()
        self.secret_number = None
        self.attempts = 0
        self.max_attempts = 0
        self.difficulty = None
        self.range_start = 1
        self.range_end = 100
        self.previous_guesses = []
        self.game_start_time = None
        self.game_end_time = None
        self.hints_enabled = True
        
    def load_stats(self) -> Dict:
        """Load game statistics from file"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self.init_stats()
        return self.init_stats()
    
    def init_stats(self) -> Dict:
        """Initialize statistics structure"""
        return {
            'total_games': 0,
            'total_wins': 0,
            'total_losses': 0,
            'best_score': None,  # least attempts in a win
            'worst_score': None,  # most attempts in a win
            'total_attempts': 0,
            'games_by_difficulty': {
                'easy': {'played': 0, 'wins': 0, 'best': None},
                'medium': {'played': 0, 'wins': 0, 'best': None},
                'hard': {'played': 0, 'wins': 0, 'best': None},
                'expert': {'played': 0, 'wins': 0, 'best': None}
            },
            'history': []
        }
    
    def save_stats(self):
        """Save statistics to file"""
        try:
            # Limit history to last 100 games
            if len(self.stats['history']) > 100:
                self.stats['history'] = self.stats['history'][-100:]
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving statistics: {e}")
    
    def set_difficulty(self, difficulty: str):
        """Set game difficulty"""
        if difficulty not in self.DIFFICULTIES:
            raise ValueError(f"Invalid difficulty. Choose from: {', '.join(self.DIFFICULTIES.keys())}")
        
        self.difficulty = difficulty
        config = self.DIFFICULTIES[difficulty]
        self.range_start, self.range_end = config['range']
        self.max_attempts = config['max_attempts']
        self.hints_enabled = config['hints']
        
    def generate_number(self):
        """Generate the secret number"""
        self.secret_number = random.randint(self.range_start, self.range_end)
        self.attempts = 0
        self.previous_guesses = []
        self.game_start_time = datetime.now()
        self.game_end_time = None
        
    def make_guess(self, guess: int) -> Dict:
        """
        Process a guess and return feedback
        
        Returns:
            dict: Contains feedback, hints, and game status
        """
        self.attempts += 1
        self.previous_guesses.append(guess)
        
        result = {
            'correct': False,
            'game_over': False,
            'won': False,
            'message': '',
            'hint': '',
            'attempts_left': self.max_attempts - self.attempts
        }
        
        if guess == self.secret_number:
            self.game_end_time = datetime.now()
            result['correct'] = True
            result['won'] = True
            result['game_over'] = True
            result['message'] = f"🎉 Congratulations! You guessed it in {self.attempts} attempts!"
            self.update_stats(win=True)
            return result
        
        # Provide feedback
        if guess < self.secret_number:
            result['message'] = "📈 Too low! Try a higher number."
        else:
            result['message'] = "📉 Too high! Try a lower number."
        
        # Provide hints if enabled
        if self.hints_enabled:
            result['hint'] = self.generate_hint()
        
        # Check if game over due to max attempts
        if self.attempts >= self.max_attempts:
            result['game_over'] = True
            result['won'] = False
            result['message'] = f"😔 Game Over! The number was {self.secret_number}."
            self.game_end_time = datetime.now()
            self.update_stats(win=False)
        
        return result
    
    def generate_hint(self) -> str:
        """Generate a helpful hint"""
        if self.secret_number is None:
            return ""
        
        hints = []
        
        # Parity hint
        if self.secret_number % 2 == 0:
            hints.append("The number is even")
        else:
            hints.append("The number is odd")
        
        # Range narrowing hint
        if self.previous_guesses:
            min_guess = min(self.previous_guesses)
            max_guess = max(self.previous_guesses)
            
            if min_guess < self.secret_number < max_guess:
                hints.append(f"The number is between {min_guess} and {max_guess}")
            elif self.secret_number < min_guess:
                hints.append(f"The number is less than {min_guess}")
            elif self.secret_number > max_guess:
                hints.append(f"The number is greater than {max_guess}")
        
        # Divisibility hint (if number is divisible by 3, 5, or 10)
        if self.secret_number % 3 == 0:
            hints.append("The number is divisible by 3")
        if self.secret_number % 5 == 0:
            hints.append("The number is divisible by 5")
        if self.secret_number % 10 == 0:
            hints.append("The number is divisible by 10")
        
        # Multi-digit hint
        if self.secret_number >= 100:
            hints.append("The number has 3 digits")
        elif self.secret_number >= 10:
            hints.append("The number has 2 digits")
        
        # Return a random hint from available ones
        if hints:
            return f"💡 Hint: {random.choice(hints)}"
        return ""
    
    def update_stats(self, win: bool):
        """Update game statistics"""
        self.stats['total_games'] += 1
        
        if win:
            self.stats['total_wins'] += 1
            
            # Update best score
            if (self.stats['best_score'] is None or 
                self.attempts < self.stats['best_score']):
                self.stats['best_score'] = self.attempts
            
            # Update worst score
            if (self.stats['worst_score'] is None or 
                self.attempts > self.stats['worst_score']):
                self.stats['worst_score'] = self.attempts
        else:
            self.stats['total_losses'] += 1
        
        self.stats['total_attempts'] += self.attempts
        
        # Update difficulty-specific stats
        diff_stats = self.stats['games_by_difficulty'][self.difficulty]
        diff_stats['played'] += 1
        if win:
            diff_stats['wins'] += 1
            if diff_stats['best'] is None or self.attempts < diff_stats['best']:
                diff_stats['best'] = self.attempts
        
        # Add game to history
        game_record = {
            'difficulty': self.difficulty,
            'number': self.secret_number,
            'attempts': self.attempts,
            'won': win,
            'max_attempts': self.max_attempts,
            'range': [self.range_start, self.range_end],
            'duration': (self.game_end_time - self.game_start_time).total_seconds(),
            'timestamp': self.game_start_time.isoformat()
        }
        self.stats['history'].append(game_record)
        
        self.save_stats()
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        stats = self.stats.copy()
        
        # Calculate win rate
        if stats['total_games'] > 0:
            stats['win_rate'] = (stats['total_wins'] / stats['total_games']) * 100
        else:
            stats['win_rate'] = 0
        
        # Calculate average attempts
        if stats['total_wins'] > 0:
            stats['avg_attempts'] = stats['total_attempts'] / stats['total_wins']
        else:
            stats['avg_attempts'] = 0
        
        return stats

def display_welcome():
    """Display welcome message and game rules"""
    print("\n" + "="*60)
    print("🔢 NUMBER GUESSING GAME 🔢")
    print("="*60)
    print("\n🎯 OBJECTIVE:")
    print("  Guess the secret number within the allowed attempts!")
    print("\n📊 DIFFICULTY LEVELS:")
    print("  Easy    : 1-50    , 10 attempts, hints available")
    print("  Medium  : 1-100   , 7 attempts, hints available")
    print("  Hard    : 1-200   , 5 attempts, no hints")
    print("  Expert  : 1-500   , 4 attempts, no hints")
    print("\n💡 TIPS:")
    print("  • Start with a number in the middle of the range")
    print("  • Pay attention to the feedback (too high/low)")
    print("  • Use hints wisely if available")
    print("="*60)

def display_statistics(game: GuessGame):
    """Display game statistics"""
    stats = game.get_statistics()
    
    print("\n" + "="*60)
    print("📊 GAME STATISTICS")
    print("="*60)
    print(f"Total Games Played: {stats['total_games']}")
    print(f"Games Won: {stats['total_wins']}")
    print(f"Games Lost: {stats['total_losses']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    
    if stats['total_wins'] > 0:
        print(f"Best Score (least attempts): {stats['best_score']}")
        print(f"Worst Score (most attempts): {stats['worst_score']}")
        print(f"Average Attempts (wins only): {stats['avg_attempts']:.1f}")
    
    print("\n--- BY DIFFICULTY ---")
    for difficulty, data in stats['games_by_difficulty'].items():
        if data['played'] > 0:
            win_rate = (data['wins'] / data['played']) * 100
            best = f"Best: {data['best']} attempts" if data['best'] else "No wins yet"
            print(f"{difficulty.capitalize():8} : {data['played']} played, {win_rate:.1f}% win rate, {best}")
        else:
            print(f"{difficulty.capitalize():8} : Not played yet")
    
    print("="*60)

def display_game_history(game: GuessGame):
    """Display game history"""
    history = game.stats['history']
    
    if not history:
        print("\nNo games played yet.")
        return
    
    print("\n" + "="*60)
    print("📜 GAME HISTORY (Last 10 games)")
    print("="*60)
    
    # Show last 10 games in reverse (newest first)
    for game_record in reversed(history[-10:]):
        result = "✅ Won" if game_record['won'] else "❌ Lost"
        duration = f"{game_record['duration']:.1f}s"
        print(f"{game_record['timestamp'][:16]} | {game_record['difficulty'].upper():6} | "
              f"Number: {game_record['number']:3} | Attempts: {game_record['attempts']:2}/{game_record['max_attempts']} | "
              f"{result:5} | {duration}")
    print("="*60)

def play_game():
    """Main game loop"""
    game = GuessGame()
    
    while True:
        display_welcome()
        
        # Select difficulty
        while True:
            difficulty = input("\nSelect difficulty (easy/medium/hard/expert): ").strip().lower()
            if difficulty in game.DIFFICULTIES:
                game.set_difficulty(difficulty)
                break
            print("Invalid difficulty. Please choose from: easy, medium, hard, expert")
        
        # Start game
        game.generate_number()
        print(f"\n🎮 Game started! I'm thinking of a number between {game.range_start} and {game.range_end}.")
        print(f"   You have {game.max_attempts} attempts. Good luck!")
        print("   (Type 'hint' for a hint, 'stats' for statistics, 'history' for game history, or 'quit' to exit)")
        
        # Game loop
        game_over = False
        while not game_over:
            # Display previous guesses
            if game.previous_guesses:
                print(f"\nPrevious guesses: {', '.join(map(str, game.previous_guesses))}")
            
            # Get user input
            user_input = input(f"\nAttempt {game.attempts + 1}/{game.max_attempts}: ").strip().lower()
            
            if user_input == 'quit':
                print(f"\n👋 Game abandoned. The number was {game.secret_number}.")
                return
            elif user_input == 'hint':
                if game.hints_enabled:
                    hint = game.generate_hint()
                    if hint:
                        print(hint)
                    else:
                        print("No hints available right now.")
                else:
                    print("❌ Hints are disabled for this difficulty level!")
                continue
            elif user_input == 'stats':
                display_statistics(game)
                continue
            elif user_input == 'history':
                display_game_history(game)
                continue
            
            # Process guess
            try:
                guess = int(user_input)
                
                # Validate guess is within range
                if not (game.range_start <= guess <= game.range_end):
                    print(f"⚠️ Please enter a number between {game.range_start} and {game.range_end}.")
                    continue
                
                result = game.make_guess(guess)
                print(result['message'])
                if result['hint']:
                    print(result['hint'])
                if result['game_over']:
                    game_over = True
                    
            except ValueError:
                print("❌ Please enter a valid number!")
                continue
        
        # Display final results
        if result['won']:
            print(f"\n🎉 You won in {game.attempts} attempts!")
        else:
            print(f"\n💪 Better luck next time!")
        
        # Show game options
        print("\n" + "="*60)
        print("GAME OPTIONS:")
        print("  1. Play again")
        print("  2. View statistics")
        print("  3. View game history")
        print("  4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            continue
        elif choice == '2':
            display_statistics(game)
            if input("\nPress Enter to continue, or 'q' to quit: ").strip().lower() == 'q':
                break
        elif choice == '3':
            display_game_history(game)
            if input("\nPress Enter to continue, or 'q' to quit: ").strip().lower() == 'q':
                break
        else:
            break
    
    print("\n👋 Thanks for playing! See you next time!")

def quick_game():
    """Quick play mode with default settings"""
    print("\n" + "="*60)
    print("⚡ QUICK PLAY MODE ⚡")
    print("="*60)
    print("Difficulty: Medium (1-100, 7 attempts)")
    print("="*60)
    
    game = GuessGame()
    game.set_difficulty('medium')
    game.generate_number()
    
    print(f"\nI'm thinking of a number between 1 and 100. You have 7 attempts!")
    
    while game.attempts < game.max_attempts:
        try:
            guess = int(input(f"Attempt {game.attempts + 1}/{game.max_attempts}: "))
            result = game.make_guess(guess)
            print(result['message'])
            if result['game_over']:
                if result['won']:
                    print(f"🎉 You won in {game.attempts} attempts!")
                else:
                    print(f"The number was {game.secret_number}.")
                break
        except ValueError:
            print("Please enter a valid number!")
    
    if not result['game_over']:
        print(f"\n😔 Game Over! The number was {game.secret_number}.")

def main():
    """Main program entry point"""
    print("\n" + "="*60)
    print("🎯 WELCOME TO THE NUMBER GUESSING GAME! 🎯")
    print("="*60)
    
    while True:
        print("\nMAIN MENU:")
        print("  1. Play Game")
        print("  2. Quick Play (Medium difficulty)")
        print("  3. View Statistics")
        print("  4. View Game History")
        print("  5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            play_game()
        elif choice == '2':
            quick_game()
        elif choice == '3':
            game = GuessGame()
            display_statistics(game)
            input("\nPress Enter to continue...")
        elif choice == '4':
            game = GuessGame()
            display_game_history(game)
            input("\nPress Enter to continue...")
        elif choice == '5':
            print("\n👋 Thanks for playing! Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()