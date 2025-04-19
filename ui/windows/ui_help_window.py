import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFileDialog, QSizePolicy)
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize, QPointF
from utils.get_resource_path import get_resource_path


class HelpWindow(QWidget):
    """Displays the help PDF in a scrollable viewer with modern UI elements."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help")
        self.setGeometry(250, 250, 900, 600)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLabel#pageLabel {
                font-size: 14px;
                color: #555555;
                padding: 4px 8px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Create the PDF viewer
        self.pdf_viewer = QPdfView(self)
        layout.addWidget(self.pdf_viewer, 1)

        # Create and load the PDF document
        self.pdf_document = QPdfDocument(self)
        pdf_path = get_resource_path(os.path.join("assets", "resources", "FAQ.pdf"))

        # Control bar at the bottom
        control_bar = QHBoxLayout()
        control_bar.setContentsMargins(0, 0, 0, 0)
        control_bar.setSpacing(10)

        # Navigation buttons
        self.prev_button = QPushButton()
        self.prev_button.setIcon(QIcon.fromTheme("go-previous"))
        self.prev_button.setToolTip("Previous page")
        self.prev_button.setFixedSize(32, 32)
        self.prev_button.clicked.connect(self.go_to_previous_page)

        self.next_button = QPushButton()
        self.next_button.setIcon(QIcon.fromTheme("go-next"))
        self.next_button.setToolTip("Next page")
        self.next_button.setFixedSize(32, 32)
        self.next_button.clicked.connect(self.go_to_next_page)

        # Page number label
        self.page_label = QLabel("Page 1/1")
        self.page_label.setObjectName("pageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Download button
        self.download_button = QPushButton(" Download PDF")
        self.download_button.setIcon(QIcon.fromTheme("document-save"))
        self.download_button.setIconSize(QSize(16, 16))
        self.download_button.clicked.connect(self.download_pdf)

        # Add widgets to control bar
        control_bar.addWidget(self.prev_button)
        control_bar.addWidget(self.next_button)
        control_bar.addWidget(self.page_label)
        control_bar.addWidget(self.download_button)

        layout.addLayout(control_bar)

        # Check if the PDF path exists and load the document
        if os.path.exists(pdf_path):
            try:
                if self.pdf_document.load(pdf_path):
                    self.pdf_viewer.setDocument(self.pdf_document)
                    self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
                    self.update_page_controls()

                    # Connect page change signal
                    self.pdf_viewer.pageNavigator().currentPageChanged.connect(self.update_page_controls)
                else:
                    raise Exception("Failed to load PDF document.")
            except Exception as e:
                warning_label = QLabel(f"⚠️ Error loading PDF: {str(e)}")
                warning_label.setStyleSheet("color: red; font-weight: bold;")
                layout.insertWidget(0, warning_label)
                print(f"⚠️ Error loading PDF: {str(e)}")
                self.disable_controls()
        else:
            warning_label = QLabel("⚠️ Help file not found!")
            warning_label.setStyleSheet("color: red; font-weight: bold;")
            layout.insertWidget(0, warning_label)
            print(f"⚠️ Help file not found at: {pdf_path}")
            self.disable_controls()

    def update_page_controls(self, page_number=None):
        """Update the page controls and label."""
        if not self.pdf_document:
            return

        if page_number is None:
            nav = self.pdf_viewer.pageNavigator()
            if nav:
                page_number = nav.currentPage()
            else:
                page_number = 0

        total_pages = self.pdf_document.pageCount()
        self.page_label.setText(f"Page {page_number + 1}/{total_pages}")

        # Enable/disable navigation buttons based on current page
        self.prev_button.setEnabled(page_number > 0)
        self.next_button.setEnabled(page_number < total_pages - 1)

    def go_to_previous_page(self):
        """Navigate to the previous page."""
        if not self.pdf_document:
            return

        nav = self.pdf_viewer.pageNavigator()
        current_page = nav.currentPage()
        if current_page > 0:
            nav.jump(current_page - 1, QPointF())

    def go_to_next_page(self):
        """Navigate to the next page."""
        if not self.pdf_document:
            return

        nav = self.pdf_viewer.pageNavigator()
        current_page = nav.currentPage()
        if current_page < self.pdf_document.pageCount() - 1:
            nav.jump(current_page + 1, QPointF())

    def disable_controls(self):
        """Disable controls when no PDF is loaded."""
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.download_button.setEnabled(False)

    def download_pdf(self):
        """Open file dialog to save the PDF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "FAQ.pdf", "PDF Files (*.pdf)"
        )
        if file_path:
            pdf_path = get_resource_path(os.path.join("assets", "resources", "FAQ.pdf"))
            try:
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()
                with open(file_path, "wb") as f:
                    f.write(pdf_content)
                print(f"📥 PDF saved to {file_path}")
            except Exception as e:
                print(f"⚠️ Error saving file: {e}")

    def closeEvent(self, event):
        """Free memory when the help window is closed."""
        print("🧹 Cleaning up Help Window memory...")
        self.pdf_document = None
        self.pdf_viewer.setDocument(None)
        event.accept()