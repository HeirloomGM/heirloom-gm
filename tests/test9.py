import sys
from PyQt6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
from rich.console import Console
from rich.text import Text

class ConsoleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Console Output")
        
        # Create a text edit widget to show console output
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        
        # Set the layout for the window
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        
        self.console = Console(file=self)
        
        # Redirect stdout to this widget
        sys.stdout = self.console

    def write(self, text):
        # Append text to the QTextEdit widget
        self.text_edit.moveCursor(self.text_edit.textCursor().End)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(self.text_edit.textCursor().End)
        self.text_edit.ensureCursorVisible()

    def flush(self):
        pass  # Required for the Console object, but does nothing here

    def animate_output(self):
        # Example of animating some colored text
        text = Text("Hello World", style="bold magenta on black")
        self.console.print(text)

        # Simulate an animation
        QTimer.singleShot(1000, lambda: self.console.print(Text("This is animated!", style="bold green")))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = ConsoleWindow()
    window.resize(600, 400)
    window.show()
    
    # Simulate console output with animation
    window.animate_output()
    
    sys.exit(app.exec())
