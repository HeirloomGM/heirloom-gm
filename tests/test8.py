import sys
import tkinter as tk
from tkinter import scrolledtext

class Console(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Console Log")

        # Create a scrolled text widget to display logs
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', height=20, width=80)
        self.text_area.pack(expand=True, fill='both')

        # Redirect stdout and stderr to the text area
        sys.stdout = TextRedirector(self.text_area, self.write_to_console)
        sys.stderr = TextRedirector(self.text_area, self.write_to_console)

    def write_to_console(self, message, tag=None):
        self.text_area.configure(state='normal')  # Make the text area editable
        self.text_area.insert(tk.END, message, tag)
        self.text_area.configure(state='disabled')  # Make it read-only again
        self.text_area.see(tk.END)  # Scroll to the end


class TextRedirector:
    def __init__(self, text_widget, write_method):
        self.text_widget = text_widget
        self.write_method = write_method

    def write(self, message):
        self.write_method(message)

    def flush(self):
        pass


if __name__ == "__main__":
    console_app = Console()
    console_app.mainloop()
