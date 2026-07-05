class TemperatureConverter:
    """A class to handle temperature conversions between Celsius, Fahrenheit, and Kelvin"""
    
    # Conversion formulas as class methods
    @staticmethod
    def celsius_to_fahrenheit(celsius):
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32
    
    @staticmethod
    def celsius_to_kelvin(celsius):
        """Convert Celsius to Kelvin"""
        return celsius + 273.15
    
    @staticmethod
    def fahrenheit_to_celsius(fahrenheit):
        """Convert Fahrenheit to Celsius"""
        return (fahrenheit - 32) * 5/9
    
    @staticmethod
    def fahrenheit_to_kelvin(fahrenheit):
        """Convert Fahrenheit to Kelvin"""
        return (fahrenheit - 32) * 5/9 + 273.15
    
    @staticmethod
    def kelvin_to_celsius(kelvin):
        """Convert Kelvin to Celsius"""
        return kelvin - 273.15
    
    @staticmethod
    def kelvin_to_fahrenheit(kelvin):
        """Convert Kelvin to Fahrenheit"""
        return (kelvin - 273.15) * 9/5 + 32
    
    @classmethod
    def convert(cls, value, from_unit):
        """
        Convert temperature from one unit to both other units
        
        Args:
            value: Temperature value to convert
            from_unit: Original unit ('C', 'F', or 'K')
        
        Returns:
            dict: Dictionary with converted values
        """
        value = float(value)
        from_unit = from_unit.upper().strip()
        
        # Validate unit
        if from_unit not in ['C', 'F', 'K']:
            raise ValueError("Invalid unit. Use 'C', 'F', or 'K'")
        
        # Convert to Celsius first (as base unit)
        if from_unit == 'C':
            celsius = value
        elif from_unit == 'F':
            celsius = cls.fahrenheit_to_celsius(value)
        elif from_unit == 'K':
            celsius = cls.kelvin_to_celsius(value)
        
        # Convert from Celsius to other units
        fahrenheit = cls.celsius_to_fahrenheit(celsius)
        kelvin = cls.celsius_to_kelvin(celsius)
        
        return {
            'celsius': celsius,
            'fahrenheit': fahrenheit,
            'kelvin': kelvin
        }
    
    @classmethod
    def convert_batch(cls, values, from_unit):
        """Convert multiple values at once"""
        results = []
        for value in values:
            try:
                result = cls.convert(value, from_unit)
                results.append(result)
            except ValueError as e:
                results.append({'error': str(e), 'original': value})
        return results

def display_conversion_table(original_value, from_unit, conversions):
    """Display conversion results in a formatted table"""
    
    # Get unit display names
    unit_names = {
        'C': 'Celsius',
        'F': 'Fahrenheit',
        'K': 'Kelvin'
    }
    
    from_unit_upper = from_unit.upper()
    original_unit_name = unit_names.get(from_unit_upper, from_unit_upper)
    
    print("\n" + "="*60)
    print(f"TEMPERATURE CONVERSION RESULTS")
    print("="*60)
    print(f"Original: {original_value}° {original_unit_name}")
    print("-"*60)
    
    # Display each conversion
    for unit, value in conversions.items():
        unit_display = unit_names.get(unit[0].upper(), unit)
        symbol = '°' if unit != 'kelvin' else ' K'
        print(f"{unit_display:12} : {value:.2f}{symbol}")
    
    print("="*60)

def display_help():
    """Display help information about temperature scales"""
    print("\n" + "="*60)
    print("TEMPERATURE SCALES REFERENCE")
    print("="*60)
    print("Celsius (°C)    : Water freezes at 0°C, boils at 100°C")
    print("Fahrenheit (°F) : Water freezes at 32°F, boils at 212°F")
    print("Kelvin (K)      : Absolute zero at 0K, water freezes at 273.15K")
    print("="*60)
    print("\nCommon temperature points:")
    print("  Absolute Zero: -273.15°C, -459.67°F, 0K")
    print("  Water Freezes: 0°C, 32°F, 273.15K")
    print("  Body Temp:    37°C, 98.6°F, 310.15K")
    print("  Water Boils:  100°C, 212°F, 373.15K")
    print("="*60)

def validate_temperature(value, unit):
    """Validate temperature against physical constraints"""
    unit = unit.upper()
    value = float(value)
    
    if unit == 'K' and value < 0:
        return False, "Temperature in Kelvin cannot be negative (absolute zero is 0K)"
    if unit == 'C' and value < -273.15:
        return False, "Temperature in Celsius cannot be below absolute zero (-273.15°C)"
    if unit == 'F' and value < -459.67:
        return False, "Temperature in Fahrenheit cannot be below absolute zero (-459.67°F)"
    
    return True, "Valid temperature"

def get_user_input():
    """Get and validate user input"""
    while True:
        try:
            # Get temperature value
            temp_input = input("\nEnter temperature value (or 'help' for reference): ").strip()
            
            if temp_input.lower() == 'help':
                display_help()
                continue
            
            if temp_input.lower() == 'quit' or temp_input.lower() == 'exit':
                return None, None, True
            
            value = float(temp_input)
            
            # Get unit
            print("\nAvailable units:")
            print("  C - Celsius")
            print("  F - Fahrenheit")
            print("  K - Kelvin")
            unit = input("Enter original unit (C/F/K): ").strip().upper()
            
            if unit not in ['C', 'F', 'K']:
                print("Invalid unit. Please enter C, F, or K.")
                continue
            
            # Validate temperature
            is_valid, message = validate_temperature(value, unit)
            if not is_valid:
                print(f"Invalid temperature: {message}")
                continue
            
            return value, unit, False
            
        except ValueError:
            print("Invalid input. Please enter a numeric temperature value.")
            continue

def interactive_mode():
    """Run the program in interactive mode"""
    converter = TemperatureConverter()
    
    print("="*60)
    print("TEMPERATURE CONVERTER")
    print("="*60)
    print("Type 'help' for temperature scale reference")
    print("Type 'quit' or 'exit' to exit the program")
    print("="*60)
    
    while True:
        value, unit, should_exit = get_user_input()
        
        if should_exit:
            print("\nThank you for using the Temperature Converter!")
            break
        
        if value is None:
            continue
        
        try:
            # Perform conversion
            conversions = converter.convert(value, unit)
            
            # Display results
            display_conversion_table(value, unit, conversions)
            
            # Ask if user wants to continue
            print("\nPress Enter to convert another temperature, or type 'quit' to exit")
            response = input().strip().lower()
            if response in ['quit', 'exit', 'q']:
                print("\nThank you for using the Temperature Converter!")
                break
                
        except ValueError as e:
            print(f"Error: {e}")
            continue

def batch_mode():
    """Run the program in batch mode for multiple conversions"""
    print("\n--- BATCH CONVERSION MODE ---")
    print("Enter multiple temperatures separated by spaces or commas")
    
    try:
        # Get multiple values
        values_input = input("Enter temperatures: ").strip()
        values = []
        for val in values_input.replace(',', ' ').split():
            try:
                values.append(float(val))
            except ValueError:
                print(f"Skipping invalid value: '{val}'")
        
        if not values:
            print("No valid temperatures entered.")
            return
        
        # Get unit
        unit = input("Enter unit for all values (C/F/K): ").strip().upper()
        if unit not in ['C', 'F', 'K']:
            print("Invalid unit.")
            return
        
        # Perform batch conversion
        converter = TemperatureConverter()
        results = converter.convert_batch(values, unit)
        
        # Display results
        print("\n" + "="*60)
        print("BATCH CONVERSION RESULTS")
        print("="*60)
        
        for i, result in enumerate(results, 1):
            if 'error' in result:
                print(f"{i}. {result['original']}: Error - {result['error']}")
            else:
                print(f"{i}. {result['original']}°{unit} → "
                      f"{result['celsius']:.2f}°C, "
                      f"{result['fahrenheit']:.2f}°F, "
                      f"{result['kelvin']:.2f}K")
        
        print("="*60)
        
    except Exception as e:
        print(f"Error in batch mode: {e}")

def main():
    """Main program entry point"""
    while True:
        print("\n" + "="*60)
        print("TEMPERATURE CONVERTER MENU")
        print("="*60)
        print("1. Interactive Mode (Single conversion)")
        print("2. Batch Mode (Multiple conversions)")
        print("3. View Temperature Scale Reference")
        print("4. Exit")
        print("="*60)
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            interactive_mode()
        elif choice == '2':
            batch_mode()
        elif choice == '3':
            display_help()
            input("\nPress Enter to continue...")
        elif choice == '4':
            print("\nThank you for using the Temperature Converter!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()