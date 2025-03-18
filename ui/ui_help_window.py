import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from utils.get_resource_path import get_resource_path

class HelpWindow(QWidget):
    """Displays the help PDF in a scrollable viewer."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help")
        self.setGeometry(250, 250, 900, 600)

        layout = QVBoxLayout(self)

        # ✅ Create the PDF viewer
        self.pdf_viewer = QPdfView(self)
        layout.addWidget(self.pdf_viewer)

        # ✅ Create and load the PDF document
        self.pdf_document = QPdfDocument(self)  
        pdf_path = get_resource_path(os.path.join("assets", "resources", "FAQ.pdf"))

        if os.path.exists(pdf_path):
            self.pdf_document.load(pdf_path)  
            self.pdf_viewer.setDocument(self.pdf_document)              
            self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        else:
            warning_label = QLabel("⚠️ Help file not found!")
            layout.addWidget(warning_label)
            print(f"⚠️ Help file not found at: {pdf_path}")

        self.setLayout(layout)  

    def closeEvent(self, event):
        """Free memory when the help window is closed."""
        print("🧹 Cleaning up Help Window memory...")
        self.pdf_document = None  # ✅ Remove reference to free memory
        self.pdf_viewer.setDocument(None)  # ✅ Detach document from viewer
        event.accept()
