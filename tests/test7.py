import tkinter as tk
import sys
from io import StringIO
from rich.console import Console
from rich.text import Text

class ConsoleStream(StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, data):
        if data:
            # Insert text into the Text widget
            self.text_widget.configure(state=tk.NORMAL)
            self.text_widget.insert(tk.END, data)
            self.text_widget.configure(state=tk.DISABLED)
            # Scroll to the bottom
            self.text_widget.yview_moveto(1.0)
    
    def flush(self):
        pass

def main():
    root = tk.Tk()
    root.title("Console Window")
    
    # Create a Canvas widget
    canvas = tk.Canvas(root, bg='black')
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Create a Scrollbar widget
    scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Create a Frame widget to hold the Text widget
    frame = tk.Frame(canvas, bg='black')
    canvas.create_window((0, 0), window=frame, anchor=tk.NW)
    
    # Create a Text widget for displaying console output
    text_widget = tk.Text(frame, wrap='word', bg='black', fg='white', height=20, width=80, padx=5, pady=5)
    text_widget.pack(expand=True, fill=tk.BOTH)
    text_widget.configure(state=tk.DISABLED)
    
    # Update the Canvas scroll region
    def update_scroll_region(*args):
        canvas.config(scrollregion=canvas.bbox("all"))
    text_widget.bind("<Configure>", update_scroll_region)
    
    # Redirect stdout and stderr
    console_stream = ConsoleStream(text_widget)
    sys.stdout = console_stream
    sys.stderr = console_stream
    
    # Create a rich Console to print text directly to stdout
    rich_console = Console(file=sys.stdout, record=True)
    rich_console.print(Text.from_markup("[red]This is red text[/red]\n[green]This is green text[/green]\n[blue]This is blue text[/blue]"))
    
    root.mainloop()

if __name__ == "__main__":
    main()
