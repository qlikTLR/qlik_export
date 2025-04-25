from datetime import datetime
import textwrap

class FileWriterHelper:
    def __init__(self, file_path):
        """
        Initializes the FileWriterHelper with a file path. Opens the file in append mode.
        
        Parameters:
            file_path (str): Path to the file where the output should be written.
        """
        self.file_path = file_path

    def _write_line(self, line):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(line + "\n")

    def write_title(self, title, spacer=''):
        """
        Writes a title or section heading to the file, optionally underlined.
        
        Parameters:
            title (str): The title text.
            underline (bool): If True, writes a line under the title. Default is True.
            spacer (str): Optional indentation string for each line.
        """
        self._write_line(f"{spacer}{title}")

    def print_bullet_from_array(self, data_array, fields):
        for item in data_array:
            if len(item) != len(fields):
                self._write_line("❗ Error: The number of fields does not match the number of values in the current item.")
                continue

            for field, value in zip(fields, item):
                if isinstance(value, list):
                    value = ", ".join(value) if value else f"No {field.lower()}"
                self._write_line(f"   - {field}: {value}")
            self._write_line("")

    def print_single_array(self, data, title=None, spacer='', maxPerLine=80):
        if title:
            self._write_line(f"\n{spacer}{title}:")
        
        for key, value in data.items():
            if isinstance(value, str) and len(value) > maxPerLine:
                wrapped_text = textwrap.fill(value, width=maxPerLine)
                self._write_line(f"{spacer}{key}:")
                for line in wrapped_text.splitlines():
                    self._write_line(f"{spacer}    {line}")
            else:
                self._write_line(f"{spacer}{key}: {value}")
        self._write_line("")

    def print_array(self, data_array, title=None):
        if title:
            self._write_line(f"\n{title}:")
        
        for item in data_array:
            for key, value in item.items():
                if isinstance(value, list):
                    value = ", ".join(value) if value else f"No {key.lower()}"
                self._write_line(f"   - {key.capitalize()}: {value}")
            self._write_line("")
