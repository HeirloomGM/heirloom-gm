import atexit
import importlib.resources
import tkinter as tk
import threading
import webbrowser
from tkinter import ttk

import os
import io
import sys
import importlib

import requests
from PIL import Image, ImageTk, ImageFont, ImageDraw
from rich.console import Console
from rich.text import Text

from ..heirloom import Heirloom
from ..password_functions import *
from ..path_functions import *
from ..database_functions import *
from ..config import *


class Tile:
    """
    Represents a game in a graphical user interface.

    Args:
        image_path (str): The path to the image associated with the game.
        title (str): The title of the game.
        description (str): The description of the game.
        installed (bool): Indicates whether the game is installed or not.

    Attributes:
        image_path (str): The path to the image associated with the game.
        title (str): The title of the game.
        description (str): The description of the game.
        installed (bool): Indicates whether the game is installed or not.
    """
    def __init__(self, image_path, title, description, installed):
        self.image_path = image_path
        self.title = title
        self.description = description
        self.installed = installed


def create_tiles():
    """
    Create and return a list of Tile objects based on the games stored in the heirloom.games list.

    Returns:
        list: A list of Tile objects representing the games.
    """
    tiles = []
    for g in heirloom.games:
        image_source = os.path.join(heirloom._tmp_dir, f'{g.get("game_id")}.jpg')
        game_name = g.get('game_name')
        game_description = g.get('game_description')
        game_installed = g.get('install_dir') if g.get('install_dir') != 'Not Installed' else None
        tiles.append(Tile(image_source, game_name, game_description, game_installed))
    return tiles


def merge_game_data_with_db():
    """
    Merges game data with the database.

    This function retrieves game records from the database and updates the game data with the corresponding information.
    It iterates over each game in the `heirloom.games` list and retrieves the game record from the database based on the
    installer UUID or the game name. If a record is found, it updates the game data with the install directory and
    executable information from the record. If no record is found, it sets the install directory and executable to
    'Not Installed'.

    Note:
    - The `heirloom.games` list is modified in-place.
    - The database connection details are obtained from the `config` dictionary.

    Returns:
    None
    """
    games = heirloom.games
    for each_game in games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            record = read_game_record(config['db'], name=each_game['game_name'])
        each_game['install_dir'] = record.get('install_dir', 'Not Installed')
        each_game['executable'] = record.get('executable', 'Not Installed')
    heirloom.games = games


def download_artwork(progress_callback, on_complete):
    """
    Downloads artwork for each game in the heirloom.games list.

    Args:
        progress_callback (function): A callback function that takes two arguments: the current progress and the total number of games.
        on_complete (function): A callback function to be called after the download is finished.

    Returns:
        None
    """
    if not os.path.exists(heirloom._tmp_dir):
        os.makedirs(heirloom._tmp_dir)
    total_games = len(heirloom.games)
    for i, g in enumerate(heirloom.games):
        coverart_url = g.get('game_coverart')
        game_id = g.get('game_id')
        file_path = os.path.join(heirloom._tmp_dir, f'{game_id}.jpg')
        if not os.path.exists(file_path):
            r = requests.get(coverart_url)
            content = r.content
            if content:
                with open(file_path, 'wb') as f:
                    f.write(content)
        # Call the progress callback with the current progress
        progress_callback(i + 1, total_games)
    # Call the completion callback after the download is finished
    on_complete()


def show_progress_window():
    """
    Displays a progress window with a progress bar and label for downloading artwork.
    This function creates a progress window using tkinter library and displays a progress bar
    along with a label indicating the progress of downloading images. The progress window is
    centered on the screen and the progress bar is updated based on the current and total
    progress values. Once the download is complete, the progress window is destroyed.
    Parameters:
        None
    Returns:
        None
    """
    global progress_window, progress_bar
    
    # Create the progress window
    progress_window = tk.Tk()
    progress_window.title("Downloading Artwork")
    progress_window.geometry("300x100")
    
    # Create a progress bar
    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=280, mode="determinate")
    progress_bar.pack(pady=20, padx=10)
    
    # Create a label
    label = tk.Label(progress_window, text="Downloading images, please wait...")
    label.pack()
    
    progress_window.update_idletasks()
    
    # Center the progress window on the screen
    window_width = 300
    window_height = 100

    # Get the screen width and height
    screen_width = progress_window.winfo_screenwidth()
    screen_height = progress_window.winfo_screenheight()

    # Calculate x and y coordinates for the progress window to be centered
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Set the position of the progress window
    progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Function to update the progress bar
    def update_progress(current, total):
        progress_percentage = (current / total) * 100
        progress_window.after(0, lambda: progress_bar.config(value=progress_percentage))
        if current >= total:
            progress_window.after(0, progress_window.destroy)

    # Run the download in a separate thread
    def start_download():
        # Make sure the main loop is running
        progress_window.update_idletasks()
        download_artwork(update_progress, lambda: None)
    
    threading.Thread(target=start_download).start()
    progress_window.mainloop()


def show_about_window():
    """
    Displays the about window for the Heirloom Games Manager.

    The about window contains information about the application, including the version, developers, and license.
    It also displays the Heirloom Games Manager logo.

    Parameters:
        None

    Returns:
        None
    """
    about_window = tk.Toplevel(window, bg='black')
    about_window.title("About Heirloom Games Manager")
    about_window.geometry("400x300")  # Increased height to fit the image

    # Center the about window on the screen
    window_width = 640
    window_height = 400 # Increased height
    screen_width = about_window.winfo_screenwidth()
    screen_height = about_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    about_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Load and display the image
    logo_path = importlib.resources.files('heirloom') / 'images' / 'heirloom.png'
    logo_image = Image.open(logo_path)
    logo_image = logo_image.resize((int(logo_image.width * 0.5), int(logo_image.height * 0.5)))  # Resize if necessary
    logo_photo = ImageTk.PhotoImage(logo_image)

    # Create a label for the image
    logo_label = tk.Label(about_window, image=logo_photo, bg="black")
    logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
    logo_label.pack(pady=10)

    # Create a label with the about text
    about_text = f"Heirloom Games Manager\n\nVersion {version}\n\nDeveloped by: {authors}\n\nLicense: {license}"
    text_label = tk.Label(about_window, text=about_text, font=("Roboto", 12, "bold"), bg="black", fg="white")
    text_label.pack(pady=10)

    # Create a button to close the window
    close_button = tk.Button(about_window, text="Close", bg="green", fg="white", command=about_window.destroy)
    close_button.pack(pady=10)
    

def open_link(url):
    """
    Opens a link in the default web browser.

    This function opens a link in the default web browser using the `webbrowser` module.

    Parameters:
        url (str): The URL to open in the web browser.

    Returns:
        None
    """
    webbrowser.open(url)

    
def refresh_main_window():
    """
    Refreshes the main window by destroying the current window and creating a new one.

    This function destroys the current main window and creates a new one by calling the `create_main_window` function.

    Parameters:
        None

    Returns:
        None
    """
    global window
    window.destroy()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    login()
    fetch_games_list()
    show_progress_window()
    create_main_window()


def install_game(title):
    heirloom.install_game(title)
    heirloom.games = heirloom.refresh_games_list()
    refresh_main_window()


class RichToTkConsole(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)  # Scroll to the end of the text widget

    def flush(self):
        pass


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
    logo_path = importlib.resources.files('heirloom') / 'images' / 'heirloom.png'
    logo_image = Image.open(logo_path)
    logo_image = logo_image  # Resize logo if needed here
    logo_photo = ImageTk.PhotoImage(logo_image)
    
    logo_label = tk.Label(logo_frame, image=logo_photo, bg="black", highlightthickness=0)
    logo_label.image = logo_photo
    logo_label.bind("<Button-1>", lambda e: open_link('https://www.github.com/HeirloomGM/heirloom-gm'))
    logo_label.pack(side=tk.TOP)
    
    # Add text beneath the logo
    logo_text = tk.Label(logo_frame, text="Heirloom Games Manager", font=("Arial", 14), fg="white", bg="black")
    logo_text.pack(side=tk.TOP, pady=10)
    
    # Create a frame for the console and tiles
    main_frame = tk.Frame(window, bg="black")
    main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Create a frame for the console
    # console_frame = tk.Frame(main_frame, bg="black", highlightthickness=0, highlightbackground="black", highlightcolor="black")
    # console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # # Add a Text widget to the console frame
    # console_text = tk.Text(console_frame, bg="black", fg="white", wrap=tk.WORD, borderwidth=0, height=10)
    # console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # # Redirect stdout to the console_text widget
    # sys.stdout = RichToTkConsole(console_text)
    # sys.stderr = RichToTkConsole(console_text)
    # print('Testing stdout!')
    # console.print(Text('Testing rich console!', style='bold green'))
    
    # Create a canvas for tiles
    canvas_frame = tk.Frame(main_frame, bg="black")
    canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(canvas_frame, bg="black")
    scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    tiles_frame = tk.Frame(canvas, bg="black")
    canvas.create_window((0, 0), window=tiles_frame, anchor=tk.NW)
    
    # Simulate the create_tiles function
    tiles = create_tiles()  # Assuming it returns a list of tiles with 'image_path', 'title', 'description', and 'installed' attributes
    
    # Add the tiles to the canvas frame
    for each_tile in tiles:
        tile_frame = tk.Frame(tiles_frame, bg="black")
        tile_frame.pack(padx=10, pady=10, anchor="w")
        
        image = Image.open(each_tile.image_path)
        image = image.resize((150, 150))
        photo = ImageTk.PhotoImage(image)
        
        label_with_image = tk.Label(tile_frame, image=photo, bg="black")
        label_with_image.image = photo
        label_with_image.pack(side=tk.LEFT, padx=10, anchor="n")
        
        text_widget = tk.Text(tile_frame, wrap="word", borderwidth=0, bg="black", fg="white",
                              highlightthickness=2, highlightbackground="black", highlightcolor="white", 
                              padx=5, pady=5, width=50, cursor='arrow')
        text_widget.insert(tk.END, f"{each_tile.title}\n\n")
        text_widget.insert(tk.END, f"{each_tile.description}")
        text_widget.tag_add("bold", "1.0", "1.end")
        text_widget.tag_config("bold", font=("Roboto", 12, "bold"), foreground="white")
        text_widget.config(state="disabled")
        text_widget.config(height=7)
        text_widget.pack(side=tk.LEFT, padx=10)
        
        install_button = tk.Button(tile_frame, text="Install", bg="green", fg="white", command=lambda title=each_tile.title: install_game(title))
        install_button.pack(side=tk.LEFT, padx=10, pady=10)
        uninstall_button = tk.Button(tile_frame, text="Uninstall", bg="red", fg="white", command=lambda title=each_tile.title: uninstall_game(title))
        uninstall_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        if each_tile.installed:
            install_button.pack_forget()
            uninstall_button.pack(side=tk.LEFT, padx=10, pady=10)
        else:
            uninstall_button.pack_forget()
            install_button.pack(side=tk.LEFT, padx=10, pady=10)
    
    # Configure the canvas to scroll
    canvas_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox(tk.ALL))
    
    def on_mouse_scroll(event):
        if event.num == 4:  # Scroll up
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Scroll down
            canvas.yview_scroll(1, "units")

    canvas.bind("<Button-4>", on_mouse_scroll)
    canvas.bind("<Button-5>", on_mouse_scroll)

    window.mainloop()


def main():
    """
    This function is the entry point of the program.
    It shows a progress window and creates the main window.
    """
    show_progress_window()
    create_main_window()


def login():
    # Login to Heirloom Games Manager
    try:
        with console.status(Text('Logging in...', style='bold')):
            user_id = heirloom.login()
    except Exception as e:
        console.print(Text('Failed to login. Exiting...', style='bold red'))
        raise(e)


def fetch_games_list():
    # Fetch games list from Heirloom server
    try:
        with console.status(Text('Fetching games list...', style='bold')):
            heirloom.refresh_games_list()
        config['db'] = init_games_db(config_dir, heirloom.games)
        with console.status(Text('Merging game data with database...', style='bold')):
            merge_game_data_with_db()
        with console.status(Text('Refreshing game installation status...', style='bold')):
            refresh_game_installation_status(config['db'])
    except Exception as e:
        console.print(Text('Failed to fetch games list. Exiting...', style='bold red'))
        raise(e)


@atexit.register
def cleanup_temp_dir():
    """
    Cleanup the temporary directory.

    This function is registered as an atexit handler and will be called when the program exits.
    It calls the `cleanup_temp_dir` function from the `heirloom` module to perform the cleanup.
    """
    heirloom.cleanup_temp_dir()


# Import necessary libraries
console = Console()

# Get metadata information from the distribution package
distribution = importlib.metadata.distribution('heirloom')
metadata = distribution.metadata
version = metadata.get('Version', 'N/A')
license = metadata.get('License', 'N/A')
authors = metadata.get('Author', 'N/A')

# Set up configuration directory and encryption key
config_dir = os.path.expanduser('~/.config/heirloom/')
encryption_key = get_encryption_key()

# Check if encryption key exists, if not create a new one
if not encryption_key:
    console.print(Text('No encryption key found. Creating a new one.', style='bold red'))
    set_encryption_key()
    encryption_key = get_encryption_key()

# Get configuration from config file
configparser = get_config(config_dir)
config = dict(configparser['HeirloomGM'])

# Create an instance of Heirloom class with the configuration
heirloom = Heirloom(**config)
login()
fetch_games_list()
