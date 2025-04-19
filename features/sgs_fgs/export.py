# features/export.py
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
            # Save the plotted graph as the first page
            pdf.savefig(canvas.figure)

            # Prepare table data
            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
            data = []
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # === Pagination Settings ===
            rows_per_page = 25
            cell_width = 1.0 / len(headers)
            cell_height = 0.03  # Consistent height for all rows
            header_height = 0.06  # Taller header

            total_pages = (len(data) + rows_per_page - 1) // rows_per_page

            for page in range(total_pages):
                from matplotlib.pyplot import figure
                fig = figure(figsize=(8.3, 11.7))  # A4 size
                ax = fig.add_subplot(111)
                ax.axis('off')

                from matplotlib.table import Table
                tbl = Table(ax, bbox=[0, 0, 1, 1])

                # Slice the data for the current page
                start_idx = page * rows_per_page
                end_idx = start_idx + rows_per_page
                page_data = data[start_idx:end_idx]

                # Add header row
                for col, header in enumerate(headers):
                    tbl.add_cell(0, col, cell_width, header_height, text=header,
                                 loc='center', facecolor='#DDDDDD')
                    cell = tbl[(0, col)]
                    cell.set_text_props(fontweight='bold', wrap=True)

                # Add data rows
                for r, row_data in enumerate(page_data, start=1):
                    for c, val in enumerate(row_data):
                        tbl.add_cell(r, c, cell_width, cell_height, text=val, loc='center')

                ax.add_table(tbl)
                pdf.savefig(fig)

        QMessageBox.information(parent, "Export Successful", f"PDF saved to {path}")
    except Exception as e:
        QMessageBox.critical(parent, "PDF Export Failed", str(e))
