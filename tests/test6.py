import tkinter as tk
import io
import sys
import importlib.resources as resources
from time import sleep
from PIL import Image, ImageTk, ImageFont, ImageDraw
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
from rich.text import Text

class RichToTkConsole(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)  # Scroll to the end of the text widget

    def flush(self):
        pass

class RichProgressToTk:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def update(self, task_id, completed, total):
        progress_text = f"Task {task_id}: {completed}/{total} ({completed / total:.0%})\n"
        self.text_widget.insert(tk.END, progress_text)
        self.text_widget.see(tk.END)  # Scroll to the end of the text widget


def refresh_main_window():
    print('Pass!  Write to console.')
    
    
def show_about_window():
    print('Pass!  Write to console.')


def create_main_window():
    """
    Creates the main window for the Heirloom Games Manager application.
    This function sets up the main window with a title, size, position, menu bar, and a frame to hold the tiles.
    It also creates a canvas with a vertical scroll bar and a frame inside the canvas for the tiles.
    The tiles are added to the tiles frame, each containing an image, title, description, and install/uninstall buttons.
    The canvas is configured to scroll and the scroll wheel is bound to the canvas for scrolling functionality.
    Returns:
        None
    """
    # Set up the main window
    global window
    window = tk.Tk()
    window.title("Heirloom Games Manager")
    
    # Center the window on the screen
    window_width = 1280
    window_height = 800
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Create a menu bar
    menu_bar = tk.Menu(window)
    window.config(menu=menu_bar)
    
    # Add a File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Refresh", command=lambda: refresh_main_window())
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=window.quit)
    
    # Add a Help menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=lambda: show_about_window())
    
    # Create a frame for the logo and text
    logo_frame = tk.Frame(window, bg="black", highlightthickness=0)
    logo_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
    
    # Load and display the logo image
    logo_path = resources.files('heirloom') / 'images' / 'heirloom.png'
    logo_image = Image.open(logo_path)
    logo_image = logo_image.resize((150, 150))  # Resize logo if needed
    logo_photo = ImageTk.PhotoImage(logo_image)
    
    logo_label = tk.Label(logo_frame, image=logo_photo, bg="black", highlightthickness=0)
    logo_label.image = logo_photo
    logo_label.pack(side=tk.TOP)
    
    # Add text beneath the logo
    logo_text = tk.Label(logo_frame, text="Heirloom Games Manager", font=("Arial", 14), fg="white", bg="black")
    logo_text.pack(side=tk.TOP, pady=10)
    
    # Create a frame for the console and tiles
    main_frame = tk.Frame(window, bg="black")
    main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Create a frame for the console
    console_frame = tk.Frame(main_frame, bg="black")
    console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
    
    # Add a Text widget to the console frame
    console_text = tk.Text(console_frame, bg="black", fg="white", wrap=tk.WORD, borderwidth=0, height=10)
    console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Redirect stdout and stderr to the console_text widget
    sys.stdout = RichToTkConsole(console_text)
    sys.stderr = RichToTkConsole(console_text)
    
    # Create a Rich Console and Progress handler that writes to the Tkinter console
    rich_console = Console()
    progress_handler = RichProgressToTk(console_text)
    
    def print_rich_message(message):
        rich_console.print(message)
    
    def update_progress():
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn()
        ) as progress:
            task1 = progress.add_task("[cyan]Processing...", total=10)
            while not progress.finished:
                sleep(1)
                progress.update(task1, advance=1)
                window.update_idletasks()  # Update the Tkinter window

    # Example usage of Rich Console
    print_rich_message(Text("Hello [bold red]World[/bold red]!", justify="center"))
    
    # Start a thread to update the progress bar
    import threading
    progress_thread = threading.Thread(target=update_progress)
    progress_thread.start()
    
    window.mainloop()

if __name__ == "__main__":
    create_main_window()
