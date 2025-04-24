from datetime import datetime
import textwrap

class TerminalHelper:
    @staticmethod
    def print_bullet_from_array(data_array, fields):
        """
        Prints a structured bullet-point format for each item in a list of arrays.
        
        Parameters:
            data_array (list): A list of arrays, where each array contains the attributes for a single item.
            fields (list): A list of field names that correspond to the values in each sub-array of data_array.
        """
        for item in data_array:
            if len(item) != len(fields):
                print("❗ Error: The number of fields does not match the number of values in the current item.")
                continue

            # Printing the bullet points for the current item
            for field, value in zip(fields, item):
                if isinstance(value, list):
                    value = ", ".join(value) if value else f"No {field.lower()}"
                print(f"   - {field}: {value}")
            print()  # Blank line after each item

    @staticmethod
    def print_single_array(data, title=None, spacer='', maxPerLine=80):
        """
        Prints a formatted list of dictionary items in bullet-point format, with optional line wrapping for long text.
        
        Parameters:
            data (dict): A dictionary to print in bullet-point format.
            title (str, optional): A title to display before printing the array. Defaults to None.
            spacer (str, optional): A string to prepend to each line (for indentation). Defaults to ''.
            maxPerLine (int, optional): The maximum number of characters per line before wrapping. Defaults to 80.
        """
        if title:
            print(f"\n{spacer}{title}:")
        
        for key, value in data.items():
            # If value is a string and exceeds maxPerLine, wrap it
            if isinstance(value, str) and len(value) > maxPerLine:
                wrapped_text = textwrap.fill(value, width=maxPerLine)
                print(f"{spacer}{key}:")
                for line in wrapped_text.splitlines():
                    print(f"{spacer}    {line}")
            else:
                print(f"{spacer}{key}: {value}")
        print()  # Blank line after each item

    @staticmethod
    def print_array(data_array, title=None):
        """
        Prints a formatted list of dictionary items in bullet-point format.
        
        Parameters:
            data_array (list): A list of dictionaries to print in bullet-point format.
            title (str, optional): A title to display before printing the array. Defaults to None.
        """
        if title:
            print(f"\n{title}:")
        
        for item in data_array:
            for key, value in item.items():
                if isinstance(value, list):
                    value = ", ".join(value) if value else f"No {key.lower()}"
                print(f"   - {key.capitalize()}: {value}")
            print()  # Blank line after each item
