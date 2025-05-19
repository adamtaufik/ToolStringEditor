#export.py

import os
from datetime import datetime

from PyQt6.QtCore import QTimer
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from PyQt6.QtWidgets import QFileDialog

from utils.path_finder import get_icon_path, get_path


class PDFExporter:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.temp_files = []

    def export_to_pdf(self, trajectory_data, params, use_metric, generate_trajectory_image,
                      generate_plot_image, get_info_text, dls_values):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Save PDF Report", "", "PDF Files (*.pdf)"
            )
            if not file_path:
                return

            self.dls_values = dls_values

            # Generate temporary plot images
            trajectory_img = generate_trajectory_image()
            tension_img = generate_plot_image('tension')
            inclination_img = generate_plot_image('inclination')
            overpull_img = generate_plot_image('overpull')

            # Create PDF canvas
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            page_number = 1

            # Add trajectory plot as first page
            if trajectory_img:
                self._draw_header(c, page_number, width, height)
                self._draw_footer(c, page_number, width, height)
                self._add_title_page(c, width, height, trajectory_img)
                c.showPage()
                page_number += 1
                self._draw_header(c, page_number, width, height)
                self._draw_footer(c, page_number, width, height)

            # Add other plot pages
            page_number = self._add_plot_pages(
                c, page_number, width, height,
                [('tension', tension_img), ('inclination', inclination_img), ('overpull', overpull_img)],
                get_info_text, get_icon_path, get_path
            )

            # Add input data and survey pages
            self._add_data_pages(
                c, page_number, width, height,
                trajectory_data, params, use_metric,
                get_icon_path, get_path
            )

            c.save()

            # Cleanup temporary files
            for f in [trajectory_img, tension_img, inclination_img, overpull_img]:
                if f: os.remove(f)

            self.parent.update_btn.setText("Exported PDF!")
            QTimer.singleShot(2000, lambda: self.parent.update_btn.setText("Update All Plots"))

        except Exception as e:
            print(f"Error exporting PDF: {e}")

    def _draw_header(self, c, page_num, width, height):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 40, "Deleum Oilfield Services Sdn. Bhd.")
        logo_path = get_icon_path("logo_full")
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, width - 120, height - 60,
                        width=80, height=40, preserveAspectRatio=True, mask='auto')
        c.line(30, height - 70, width - 30, height - 70)

    def _draw_footer(self, c, page_num, width, height):
        c.setFont("Helvetica", 10)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        c.drawCentredString(width / 2, 60, f"Report generated: {date_str}")
        c.drawRightString(width - 40, 60, f"Page {page_num}")

        wirehub_path = get_path(os.path.join("assets", "backgrounds", "title.png"))
        if os.path.exists(wirehub_path):
            wirehub = ImageReader(wirehub_path)
            c.drawImage(wirehub, 40, 30, width=100, height=50, preserveAspectRatio=True, mask='auto')
        c.line(30, 80, width - 30, 80)

    # In pdf_export.py
    @staticmethod
    def add_text_section(canvas, text_lines, y_pos, width, height, page_number):
        """Adds formatted text section to PDF"""
        canvas.setFont("Helvetica", 10)
        text_obj = canvas.beginText(50, y_pos)

        for line in text_lines:
            if line.startswith("•"):
                text_obj.setFont("Helvetica-Bold", 10)
                text_obj.textOut('• ')
                text_obj.setFont("Helvetica", 10)
                text_obj.textLine(line[2:])
            else:
                text_obj.textLine(line)
            y_pos -= 14

        canvas.drawText(text_obj)
        return y_pos

    def _add_title_page(self, c, width, height, trajectory_img):
        # Add main titles
        c.setFillColorRGB(0.6, 0, 0.1)  # Burgundy color
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 100, "Deleum WireHub")
        c.setFillColorRGB(0, 0, 0)  # Reset to black
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 140, "Wireline Operation Simulation")

        # Two-column layout for metadata
        col_x = [50, width / 2 + 20]
        line_height = 14
        current_y = height - 180

        # Column 1 content
        col1 = [
            "Project: ...",
            "Prepared by: ...",
            "Client: ...",
            f"Simulation Date: {datetime.now().strftime('%Y-%m-%d')}",
            "Field: ...",
            "Location: ..."
        ]
        c.setFont("Helvetica", 12)
        for line in col1:
            c.drawString(col_x[0], current_y, line)
            current_y -= line_height

        # Column 2 content
        current_y = height - 180
        col2 = [
            "Well: ...",
            "Wire: ...",
            "Tool String: ...",
            "Weak Point: ...",
            "Country: Malaysia"
        ]
        for line in col2:
            c.drawString(col_x[1], current_y, line)
            current_y -= line_height

        # Add trajectory image
        if trajectory_img:
            img = ImageReader(trajectory_img)
            img_w, img_h = img.getSize()
            aspect = img_h / img_w
            plot_width = width - 200
            plot_height = plot_width * aspect

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, current_y - 40, "Well Trajectory Overview")
            c.drawImage(img, 50, current_y - 50 - plot_height,
                        width=plot_width, height=plot_height)

    def _add_plot_pages(self, c, page_number, width, height, plots, get_info_text, get_icon_path, get_path):
        y_pos = height - 100
        for plot_type, img_path in plots:
            if not img_path:
                continue

            img = ImageReader(img_path)
            img_w, img_h = img.getSize()
            aspect = img_h / img_w
            plot_width = width - 100
            plot_height = plot_width * aspect

            if y_pos - plot_height < 150:
                c.showPage()
                page_number += 1
                self._draw_header(c, page_number, width, height)
                self._draw_footer(c, page_number, width, height)
                y_pos = height - 100

            title = {
                'tension': 'Tension Analysis',
                'inclination': 'Trajectory Analysis',
                'overpull': 'Overpull Analysis'
            }.get(plot_type, 'Plot')

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos - 20, title)
            y_pos -= 40

            c.drawImage(img, 50, y_pos - plot_height,
                        width=plot_width, height=plot_height)
            y_pos -= plot_height + 40

            if plot_type in ['tension', 'inclination']:
                text_section = get_info_text(plot_type)
                y_pos = self.add_text_section(c, text_section, y_pos, width, height, page_number)

        return page_number

    def _add_data_pages(self, c, page_number, width, height,
                        trajectory_data, params, use_metric,
                        get_icon_path, get_path):  # Added missing parameters
        # Input Data Page
        c.showPage()
        page_number += 1
        self._draw_header(c, page_number, width, height)  # Added get_icon_path
        self._draw_footer(c, page_number, width, height)  # Added get_path

        y_pos = height - 100
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, y_pos, "Input Data")
        c.line(width / 2 - 50, y_pos - 5, width / 2 + 50, y_pos - 5)
        y_pos -= 40


        # Well Parameters
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_pos, "Well Parameters")
        c.setFont("Helvetica", 10)
        y_pos -= 20

        params_list = [
            f"Wire Speed: {params.get('speed', 'N/A')} ft/min",
            f"Stuffing Box Friction: {params.get('stuffing_box', 'N/A')} lbf",
            f"Wellhead Pressure: {params.get('pressure', 'N/A')} psi",
            f"Safe Operating Load: {params.get('safe_operating_load', 'N/A')}%",
            f"Friction Coefficient: {params.get('friction_coeff', 'N/A')}"
        ]

        for param in params_list:
            c.drawString(60, y_pos, param)
            y_pos -= 15
        y_pos -= 10

        # Survey Data Table
        if trajectory_data and 'mds' in trajectory_data:
            c.showPage()
            page_number += 1
            self._draw_header(c, page_number, width, height)
            self._draw_footer(c, page_number, width, height)

            y_pos = height - 100
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, y_pos, "Survey Data")
            c.line(width / 2 - 50, y_pos - 5, width / 2 + 50, y_pos - 5)
            y_pos -= 30

            # Table headers
            headers = ["MD", "TVD", "Inclination", "DLS"]
            col_widths = [100, 100, 100, 100]
            x_pos = 50

            c.setFont("Helvetica-Bold", 10)
            for header, col_width in zip(headers, col_widths):
                c.drawString(x_pos, y_pos, header)
                x_pos += col_width

            y_pos -= 20
            c.line(50, y_pos, width - 50, y_pos)
            y_pos -= 10

            # Table rows
            c.setFont("Helvetica", 9)
            mds = trajectory_data['mds']
            for i in range(len(mds)):
                if y_pos < 100:
                    c.showPage()
                    page_number += 1
                    self._draw_header(c, page_number, width, height)
                    self._draw_footer(c, page_number, width, height)
                    y_pos = height - 100

                md = float(mds[i])
                tvd = float(trajectory_data['tvd'][i])
                incl = float(trajectory_data['inclinations'][i])
                dls = self.dls_values[i] if i < len(self.dls_values) else 0.0

                x_pos = 50
                c.drawString(x_pos, y_pos, f"{md:.1f}")
                x_pos += col_widths[0]
                c.drawString(x_pos, y_pos, f"{tvd:.1f}")
                x_pos += col_widths[1]
                c.drawString(x_pos, y_pos, f"{incl:.1f}°")
                x_pos += col_widths[2]
                c.drawString(x_pos, y_pos, f"{dls:.1f}°/{'30m' if use_metric else '100ft'}")

                y_pos -= 15
                c.line(50, y_pos - 5, width - 50, y_pos - 5)

        return page_number