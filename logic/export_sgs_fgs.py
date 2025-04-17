# logic/export_sgs_fgs.py
import csv
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from matplotlib.backends.backend_pdf import PdfPages

def export_to_csv(table, parent=None):
    path, _ = QFileDialog.getSaveFileName(parent, "Save CSV", "", "CSV Files (*.csv)")
    if not path:
        return

    try:
        with open(path, mode='w', newline='') as file:
            writer = csv.writer(file)
            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
            writer.writerow(headers)
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)
        QMessageBox.information(parent, "Export Successful", f"Data exported to {path}")
    except Exception as e:
        QMessageBox.critical(parent, "Export Failed", str(e))


def export_to_pdf(canvas, table, parent=None):
    path, _ = QFileDialog.getSaveFileName(parent, "Save PDF", "", "PDF Files (*.pdf)")
    if not path:
        return

    try:
        with PdfPages(path) as pdf:
            # Save the plotted graph
            pdf.savefig(canvas.figure)

            # Save the table as an image
            from matplotlib.pyplot import figure
            fig = figure(figsize=(8, 6))
            ax = fig.add_subplot(111)
            ax.axis('off')
            data = [[table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]]
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            from matplotlib.table import Table
            tbl = Table(ax, bbox=[0, 0, 1, 1])
            nrows = len(data)
            ncols = len(data[0])

            width, height = 1.0 / ncols, 1.0 / nrows
            for r, row in enumerate(data):
                for c, val in enumerate(row):
                    tbl.add_cell(r, c, width, height, text=val, loc='center')
            ax.add_table(tbl)
            pdf.savefig(fig)

        QMessageBox.information(parent, "Export Successful", f"PDF saved to {path}")
    except Exception as e:
        QMessageBox.critical(parent, "PDF Export Failed", str(e))
