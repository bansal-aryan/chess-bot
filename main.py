from src.gui import ChessWindow
import sys

from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

window = ChessWindow()
window.show()

sys.exit(app.exec())