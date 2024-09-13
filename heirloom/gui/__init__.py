import tkinter as tk
import threading
from tkinter import ttk

import os
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
    def __init__(self, image_path, title, description):
        self.image_path = image_path
        self.title = title
        self.description = description


def create_tiles():
    tiles = []
    for g in heirloom.games:
        image_source = os.path.join(heirloom._tmp_dir, f'{g.get("game_id")}.jpg')
        game_name = g.get('game_name')
        game_description = g.get('game_description')
        tiles.append(Tile(image_source, game_name, game_description))
    return tiles


def merge_game_data_with_db():
    games = heirloom.games
    for each_game in games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            record = read_game_record(config['db'], name=each_game['game_name'])
        each_game['install_dir'] = record.get('install_dir', 'Not Installed')
        each_game['executable'] = record.get('executable', 'Not Installed')
    heirloom.games = games


def download_artwork(progress_callback, on_complete):
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


def render_text_image(text, font_path, size=12):
    font = ImageFont.truetype(font_path, size)
    image = Image.new('RGB', (300, 100), color='black')  # Create a blank image with black background
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), text, font=font, fill='white')  # Render the text on the image
    return image


def show_progress_window():
    global progress_window, progress_bar, window
    
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
    

def create_main_window():
    # Set up the main window
    global window
    window = tk.Tk()
    window.title("Heirloom Games Manager")
    
    # Center the progress window on the screen
    window_width = 1280
    window_height = 800

    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate x and y coordinates for the progress window to be centered
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Set the position of the progress window
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Create a menu bar
    menu_bar = tk.Menu(window)
    window.config(menu=menu_bar)
    
    # Add a File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Refresh", command=lambda: print("Refresh selected"))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=window.quit)
    
    # Add a Help menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=lambda: show_about_window())
    
    # Simulate the create_tiles function
    tiles = create_tiles()  # Assuming it returns a list of tiles with 'image_path', 'title', 'description'
    
    # Create a frame to hold the tiles
    frame = tk.Frame(window)
    frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a canvas with a vertical scroll bar
    canvas = tk.Canvas(frame, bg="black")  # Set canvas background to black
    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a frame inside the canvas for the tiles
    tiles_frame = tk.Frame(canvas, bg="black")  # Set tiles frame background to black
    canvas.create_window((0, 0), window=tiles_frame, anchor=tk.NW)

    # Define the number of lines to fit
    num_lines = 7  # Number of lines including the title

    # Add the tiles to the tiles frame
    for each_tile in tiles:
        # Create a frame for each tile
        tile_frame = tk.Frame(tiles_frame, bg="black")
        tile_frame.pack(padx=10, pady=10, anchor="w")

        # Load and resize the image (150x150)
        image = Image.open(each_tile.image_path)
        image = image.resize((150, 150))  # Updated to 150x150
        photo = ImageTk.PhotoImage(image)

        # Create the label with the image, aligning it to the top
        label_with_image = tk.Label(tile_frame, image=photo, bg="black")
        label_with_image.image = photo  # Keep a reference to avoid garbage collection
        label_with_image.pack(side=tk.LEFT, padx=10, anchor="n")  # Align with the top (anchor="n")

        # Set the width of the Text widget to 50
        text_widget_width = 50

        # Create the Text widget for complex formatting
        text_widget = tk.Text(tile_frame, wrap="word", borderwidth=0, bg="black", fg="white",
                              highlightthickness=2, highlightbackground="black", highlightcolor="white", 
                              padx=5, pady=5, width=text_widget_width, cursor='arrow')  
        text_widget.insert(tk.END, f"{each_tile.title}\n\n")  # Added extra newline for spacing
        text_widget.insert(tk.END, f"{each_tile.description}")

        # Apply tags for styling (fixed bold range)
        text_widget.tag_add("bold", "1.0", "1.end")  # Ensure the whole title is bolded
        text_widget.tag_config("bold", font=("Roboto", 12, "bold"), foreground="white")  # White bold text

        # Make the text widget read-only
        text_widget.config(state="disabled")

        # Set the height of the Text widget to fit seven lines
        text_widget.config(height=num_lines)  # Set fixed height to 7 lines

        # Pack the text widget next to the image
        text_widget.pack(side=tk.LEFT, padx=10)
        
        # Create the Install button
        install_button = tk.Button(tile_frame, text="Install", bg="green", fg="white", command=lambda title=each_tile.title: heirloom.install_game(title))
        install_button.pack(side=tk.LEFT, padx=10, pady=10)


    # Configure the canvas to scroll
    tiles_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox(tk.ALL))

    # Bind the scroll wheel to the canvas using mouse buttons 4 and 5
    def on_mouse_scroll(event):
        if event.num == 4:  # Scroll up
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Scroll down
            canvas.yview_scroll(1, "units")

    canvas.bind("<Button-4>", on_mouse_scroll)  # Bind mouse button 4 (scroll up) to the canvas
    canvas.bind("<Button-5>", on_mouse_scroll)  # Bind mouse button 5 (scroll down) to the canvas

    window.mainloop()


def main():
    show_progress_window()
    create_main_window()
    heirloom.cleanup_temp_dir()


console = Console()

distribution = importlib.metadata.distribution('heirloom')
metadata = distribution.metadata
version = metadata.get('Version', 'N/A')
license = metadata.get('License', 'N/A')
authors = metadata.get('Author', 'N/A')

config_dir = os.path.expanduser('~/.config/heirloom/')
encryption_key = get_encryption_key()
if not encryption_key:
    console.print(Text('No encryption key found. Creating a new one.', style='bold red'))
    set_encryption_key()
    encryption_key = get_encryption_key()
configparser = get_config(config_dir)
config = dict(configparser['HeirloomGM'])
heirloom = Heirloom(**config)
try:
    with console.status(Text('Logging in...', style='bold')):
        user_id = heirloom.login()
except Exception as e:
    console.print(Text('Failed to login. Exiting...', style='bold red'))
    raise(e)
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
