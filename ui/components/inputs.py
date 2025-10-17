from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QLineEdit, QTextEdit


class LimitedTextEdit(QTextEdit):
    def __init__(self, max_lines=5):
        super().__init__()
        self.max_lines = max_lines
        self.setPlaceholderText(f"Remarks (max {max_lines} lines)")
        self.setFixedHeight(4 * 20)  # Approx height for 5 lines
        self.textChanged.connect(self.limit_lines)

        # **Apply Rounded Border Style**
        self.setStyleSheet("""
            QTextEdit {
                border-radius: 8px;
                padding: 5px;
                background-color: white;
            }
        """)

    def limit_lines(self):
        """Restrict text to a maximum of `max_lines` lines."""
        text = self.toPlainText()
        lines = text.split("\n")

        if len(lines) > self.max_lines:
            # Keep only the first `max_lines` lines
            self.setPlainText("\n".join(lines[:self.max_lines]))

            # Move cursor to end of text
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.setTextCursor(cursor)


class AngleInput(QLineEdit):
    """Custom QLineEdit that only accepts numbers and appends a degree symbol (°)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ✅ Only allow numbers (supports decimals)
        self.setValidator(QDoubleValidator(0.0, 360.0, 2, notation=QDoubleValidator.Notation.StandardNotation))

        # ✅ Set placeholder text
        self.setPlaceholderText("Max Angle (°)")

        # ✅ Connect editingFinished signal to append the degree symbol
        self.editingFinished.connect(self.add_degree_symbol)

    def add_degree_symbol(self):
        """Appends the degree symbol to the number, ensuring it's formatted properly."""
        text = self.text().strip()

        # ✅ Only modify if the input is a valid number
        if text and text[-1] != "°":
            self.setText(f"{text}°")

    def keyPressEvent(self, event):
        """Override keyPressEvent to allow backspacing when degree symbol is present."""
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            if self.text().endswith("°"):
                self.setText(self.text()[:-1])  # Remove degree symbol before deleting
        super().keyPressEvent(event)
