import tkinter as tk
from PIL import ImageTk, Image

# Create a list of game data
games = [
    {
        "image_path": "path_to_image1.png",
        "name": "Game 1",
        "description": "This is the description of Game 1."
    },
    {
        "image_path": "path_to_image2.png",
        "name": "Game 2",
        "description": "This is the description of Game 2."
    },
    # Add more game data as needed
]

# Create the main window
window = tk.Tk()

# Create a tile for each game
for game in games:
    # Load the image
    image = Image.open(game["image_path"])
    image = image.resize((100, 100))  # Resize the image to 100x100
    image = ImageTk.PhotoImage(image)

    # Create a label for the image
    image_label = tk.Label(window, image=image)
    image_label.pack()

    # Create a label for the game name
    name_label = tk.Label(window, text=game["name"], font=("Arial", 14, "bold"))
    name_label.pack()

    # Create a label for the game description
    description_label = tk.Label(window, text=game["description"], font=("Arial", 12))
    description_label.pack()

    # Add some spacing between tiles
    tk.Label(window, text="").pack()

# Start the main loop
window.mainloop()