from PyQt6.QtCore import QThread, pyqtSignal

from editor.export_manager import export_to_excel


class ExportWorker(QThread):
    """Handles the export process in a separate thread."""
    finished = pyqtSignal(str)  # ✅ Emit the directory as a string

    def __init__(self, parent, excel_path, pdf_path, final_directory):
        super().__init__(parent)
        self.parent = parent
        self.excel_path = excel_path
        self.pdf_path = pdf_path
        self.final_directory = final_directory

    def run(self):
        """Runs the export features in a background thread."""
        print('running export_to_excel')
        export_to_excel(self.excel_path, self.pdf_path,
                        self.parent.client_name.text(),
                        self.parent.location.text(),
                        self.parent.well_no.text(),
                        self.parent.max_angle.text(),
                        self.parent.well_type.currentText(),
                        self.parent.job_date.date().toString("dd MMM yyyy"),
                        self.parent.operation_details.text(),
                        self.parent.comments.toPlainText(),
                        self.parent.drop_zone)

        self.finished.emit(self.final_directory)  # ✅ Emit directory when done
