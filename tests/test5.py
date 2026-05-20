import tkinter as tk

def on_mouse_wheel(event):
    print("Mouse wheel event:", event.delta)

def on_mouse_click(event):
    print(f"Mouse click event: Button {event.num} at ({event.x}, {event.y})")

def main():
    window = tk.Tk()
    window.title("Mouse Event Test")
    window.geometry("400x400")

    canvas = tk.Canvas(window, bg="black")
    canvas.pack(fill=tk.BOTH, expand=True)

    # Bind mouse wheel and button click events
    canvas.bind("<MouseWheel>", on_mouse_wheel)
    canvas.bind("<Button>", on_mouse_click)

    window.mainloop()

if __name__ == "__main__":
    main()
