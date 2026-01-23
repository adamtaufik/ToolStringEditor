import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageTemplate, Frame, \
    PageBreak
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QVBoxLayout,
    QHBoxLayout, QGroupBox, QFrame, QMessageBox, QFileDialog,
    QInputDialog, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QFileInfo
from PyQt6.QtGui import QPalette, QColor

from utils.path_finder import get_icon_path


# =========================
# TOOL LIFT CALCULATION MODEL
# =========================
class ToolLiftModel:
    def __init__(self, i):
        self.i = i
        self.calculate()

    def calculate(self):
        import math

        # =========================
        # INPUT CELLS (YELLOW)
        # =========================
        D6 = self.i["D6"]
        D14 = self.i["D14"]
        D15 = self.i["D15"]
        D16 = self.i["D16"]
        D17 = self.i["D17"]
        D18 = self.i["D18"]

        H6 = self.i["H6"]
        H7 = self.i["H7"]
        H8 = self.i["H8"]
        H9 = self.i["H9"]
        H10 = self.i["H10"]
        H11 = self.i["H11"]
        H12 = self.i["H12"]
        H13 = self.i["H13"]
        H14 = self.i["H14"]
        H15 = self.i["H15"]

        I23 = 0.0035

        # =========================
        # DERIVED VARIABLES
        # =========================
        # Fixed constants
        D9 = 0.96  # downhole density of water
        D10 = 41.1  # surface oil API
        D11 = 237  # deg F
        D13 = 0.800  # gas specific gravity
        H16 = 25  # wire friction
        H17 = 0.0035  # line friction factor
        H18 = 20  # surface pull on line

        Z7 = 0.758
        Z15 = 0.857

        # Volumes & ratios (V variables)
        V3 = 0.8
        V5 = (D11 + 60) / 2 + 460
        V6 = (D6 + (D6 + 0.45 * H13)) / 2  # D7 will be defined later
        V7 = Z7
        V8 = 0.0283 * V5 * V7 / V6
        V9 = V8 / 5.615 * 1000

        V13 = D11 + 460
        V14 = D6 + 0.45 * H13  # D7
        V15 = Z15
        V16 = 0.0283 * (V13 * V15 / V14)
        V17 = V16 / 5.615 * 1000

        # =========================
        # CALCULATED TOOL / FLUID VALUES
        # =========================
        # D7 depends on H13
        D7 = D6 + (0.45 * H13)

        # S10, S11 depend on V variables
        S10 = (0.043234 * V6 * V3) / (V5 * V7)
        S11 = (0.043234 * V14 * V3) / (V13 * V15)

        # D8 depends on S11
        D8 = S11

        # Oil & Gas calculations
        if D10 == 0:
            M11 = 0
            O10 = 0
            O11 = 0
        else:
            M11 = (D10 - 0.059175 * ((D11 - 60) * -1)) / (1 + 0.00045 * ((D11 - 60) * -1))
            O10 = 141.5 / (D10 + 131.5)
            O11 = 141.5 / (M11 + 131.5)

        D12 = O11

        # =========================
        # N & P SERIES CALCULATIONS
        # =========================
        # N5
        if D14 > 0:
            if (D17 * D15) < D14 * 1000:
                N5 = (((D14 * 1000) - (D15 * D17)) / 5.615) * V8
            else:
                N5 = 0
        else:
            N5 = ((D14 * 1000) / 5.615) * V8

        N6 = D15 * D18
        N7 = D16 * 1.05
        N8 = N5 + N6 + N7

        # P series
        P5 = N5 / N8
        P6 = N6 / N8
        P7 = N7 / N8
        P8 = P5 + P6 + P7

        # Q series
        Q5 = P5 * S10
        Q6 = P6 * D12
        Q7 = P7 * D9

        Q8 = Q5 + Q6 + Q7 if (D14 + D15 + D16) != 0 else D8

        # N14–N17
        if D14 > 0:
            if (D17 * D15) < D14 * 1000:
                N14 = (((D14 * 1000) - (D15 * D17)) / 5.615) * V16
            else:
                N14 = 0
        else:
            N14 = ((D14 * 1000) / 5.615) * V16

        N15 = D15 * D18
        N16 = D16 * 1.05
        N17 = N14 + N15 + N16

        # P14–P17
        P14 = N14 / N17
        P15 = N15 / N17
        P16 = N16 / N17
        P17 = P14 + P15 + P16

        # Q14–Q17
        Q14 = P14 * S11
        Q15 = P15 * D12
        Q16 = P16 * D9
        Q17 = Q14 + Q15 + Q16 if (D14 + D15 + D16) != 0 else D8

        # =========================
        # PRESSURE / FORCE CALCS
        # =========================
        # N23–N26
        N23 = N8 / 1.4 / (H7 ** 2 - H9 ** 2)
        N24 = N17 / 1.4 / (H8 ** 2 - H9 ** 2)
        N25 = N8 / 1.4 / (H7 ** 2 - H11 ** 2)
        N26 = N17 / 1.4 / (H8 ** 2 - H11 ** 2)

        # P23–P26
        P23 = (N23 / 3.281) / 60
        P24 = (N24 / 3.281) / 60
        P25 = (N25 / 3.281) / 60
        P26 = (N26 / 3.281) / 60

        # S23, S25
        S23 = H9 * 0.0254
        S25 = H11 * 0.0254

        # N29–N30
        N29 = ((H13 - H10) / 1000) * H14 * math.cos(H6 * 0.017453292) if H13 > H10 else 0
        N30 = H15 * math.cos(H6 * 0.017453292)

        # Q29–Q30
        Q29 = N29 - (((H11 / 24) ** 2 * 3.14152) * H13 * (Q8 * 62.43) * 0.85)
        Q30 = N30 - (((H9 / 24) ** 2 * 3.14152) * H10 * (Q17 * 62.43))

        # S29–S30
        S29 = N29 - Q29
        S30 = N30 - Q30

        # O32
        O32 = (H11 / 2) ** 2 * 3.141516 * D6

        # O36–O39
        O36 = 0 if H13 > (H12 + H10) else H10
        O37 = H10 if H13 > (H12 + H10) else 0
        O38 = H12 if H13 > H12 else H13 - H10
        O39 = H13 - (H12 + H10) if H13 > (H12 + H10) else 0

        # P36–P39
        P36 = O36 / 3.281
        P37 = O37 / 3.281
        P38 = O38 / 3.281
        P39 = O39 / 3.281

        # S36–S39
        S36 = (I23 * (Q8 * 1000) * (P23 ** 2) * 3.141516 * S23 * (P36 / 2)) if P23 < 0 else (
                I23 * (Q8 * 1000) * (-P23 ** 2) * 3.141516 * S23 * (P36 / 2))
        S37 = (I23 * (Q17 * 1000) * (P24 ** 2) * 3.141516 * S23 * (P37 / 2)) if P24 < 0 else (
                I23 * (Q17 * 1000) * (-P24 ** 2) * 3.141516 * S23 * (P37 / 2))
        S38 = (H17 * (Q8 * 1000) * (P25 ** 2) * 3.141516 * S25 * (P38 / 2)) if P25 < 0 else (
                H17 * (Q8 * 1000) * (-P25 ** 2) * 3.141516 * S25 * (P38 / 2))
        S39 = (H17 * (Q17 * 1000) * (P26 ** 2) * 3.141516 * S25 * (P39 / 2)) if P26 < 0 else (
                H17 * (Q17 * 1000) * (-P26 ** 2) * 3.141516 * S25 * (P39 / 2))

        S40 = S36 + S37 + S38 + S39

        # T36–T40
        T36 = S36 * 0.2248
        T37 = S37 * 0.2248
        T38 = S38 * 0.2248
        T39 = S39 * 0.2248
        T40 = S40 * 0.2248

        # U37, U39
        U37 = T36 + T37
        U39 = T38 + T39
        V37 = "Drag on tools" if U37 > 0 else "Lift on tools"
        V39 = "Drag on cable" if U39 > 0 else "Lift on cable"

        self.E30 = round(Q29, 1)
        self.E31 = round(Q30, 1)
        self.E32 = round(self.E30 + self.E31, 1)

        self.H27 = round(H18 * -1, 1)
        self.H28 = round(O32 * -1, 1)
        self.H29 = round(H16 * -1, 1)
        self.H30 = round(float(U39), 1)
        self.H31 = round(float(U37), 1)
        self.H32 = round(self.H27 + self.H28 + self.H29 + self.H30 + self.H31, 1)

        # O42–O44
        O42 = self.E30 + (self.H27 + self.H28 + self.H29 + self.H30)
        O43 = self.E31 + self.H31
        O44 = self.E32 + self.H32

        # =========================
        # FINAL OUTPUT CELLS
        # =========================
        self.E21 = round(O42, 0)
        self.E22 = round(O43, 0)
        self.E23 = round(O44, 0)

        # Store additional calculated values for reporting
        self.calculated_values = {
            "D7": D7,
            "D8": D8,
            "D12": D12,
            "N8": N8,
            "N17": N17,
            "Q8": Q8,
            "Q17": Q17,
            "U37": U37,
            "U39": U39,
            "V37": V37,
            "V39": V39
        }


# =========================
# REPORT INFO DIALOG
# =========================
class ReportInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Information")
        self.setModal(True)
        self.resize(400, 200)

        # Apply black font stylesheet to the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: black;
                font-weight: bold;
            }
            QLineEdit {
                color: black;
                background-color: white;
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                color: black;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

        layout = QFormLayout(self)

        # Client field
        self.client_edit = QLineEdit()
        self.client_edit.setPlaceholderText("Enter client name")
        self.client_edit.setStyleSheet("color: black;")
        layout.addRow("Client:", self.client_edit)

        # Well Number field
        self.well_edit = QLineEdit()
        self.well_edit.setPlaceholderText("Enter well number")
        self.well_edit.setStyleSheet("color: black;")
        layout.addRow("Well Number:", self.well_edit)

        # Prepared By field
        self.prepared_by_edit = QLineEdit()
        self.prepared_by_edit.setPlaceholderText("Enter your name")
        self.prepared_by_edit.setStyleSheet("color: black;")
        layout.addRow("Prepared By:", self.prepared_by_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                color: black;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_info(self):
        return {
            "client": self.client_edit.text().strip(),
            "well_number": self.well_edit.text().strip(),
            "prepared_by": self.prepared_by_edit.text().strip()
        }


# =========================
# PDF REPORT GENERATOR
# =========================
class PDFReportGenerator:
    def __init__(self, inputs, results, calculated_values, report_info):
        self.inputs = inputs
        self.results = results
        self.calculated_values = calculated_values
        self.report_info = report_info
        self.styles = getSampleStyleSheet()

        # Create custom styles with unique names
        self.create_styles()

    def create_styles(self):
        # Use unique style names to avoid conflicts
        # Main Title style
        if not hasattr(self.styles, 'MyTitle'):
            self.styles.add(ParagraphStyle(
                name='MyTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E7D32'),
                spaceAfter=30,
                alignment=TA_CENTER
            ))

        # Subtitle style
        if not hasattr(self.styles, 'ReportSubtitle'):
            self.styles.add(ParagraphStyle(
                name='ReportSubtitle',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            ))

        # Section header style
        if not hasattr(self.styles, 'ReportSectionHeader'):
            self.styles.add(ParagraphStyle(
                name='ReportSectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=12,
                spaceBefore=20
            ))

        # Footer style
        if not hasattr(self.styles, 'ReportFooter'):
            self.styles.add(ParagraphStyle(
                name='ReportFooter',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            ))

        # Table header style
        if not hasattr(self.styles, 'ReportTableHeader'):
            self.styles.add(ParagraphStyle(
                name='ReportTableHeader',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.white,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))

        # Highlight style for important results
        if not hasattr(self.styles, 'ReportHighlight'):
            self.styles.add(ParagraphStyle(
                name='ReportHighlight',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#D32F2F'),
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ))

    def header_footer(self, canvas, doc):
        # Save the canvas state
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#2E7D32'))
        canvas.drawString(inch, doc.height + inch + 0.5 * inch, "TOOL LIFT ANALYSIS REPORT")

        # Draw header line
        canvas.setStrokeColor(colors.HexColor('#1976D2'))
        canvas.setLineWidth(1)
        canvas.line(inch, doc.height + inch + 0.1 * inch, doc.width + inch, doc.height + inch + 0.1 * inch)

        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))

        # Left footer - Company info
        canvas.drawString(inch, 0.5 * inch, "DELEUM OILFIELD SERVICES SDN BHD")
        canvas.drawString(inch, 0.3 * inch, "Slickline Well Services/Asset Integrity Solutions")
        canvas.drawString(inch, 0.1 * inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Right footer - Page info
        page_num = canvas.getPageNumber()
        canvas.drawRightString(doc.width + inch, 0.5 * inch, f"Client: {self.report_info.get('client', 'N/A')}")
        canvas.drawRightString(doc.width + inch, 0.3 * inch, f"Well: {self.report_info.get('well_number', 'N/A')}")
        canvas.drawRightString(doc.width + inch, 0.1 * inch, f"Page {page_num}")

        # Draw footer line
        canvas.setStrokeColor(colors.HexColor('#1976D2'))
        canvas.setLineWidth(0.5)
        canvas.line(inch, 0.7 * inch, doc.width + inch, 0.7 * inch)

        # Restore the canvas state
        canvas.restoreState()

    def create_title_page(self, elements):
        logo_path = get_icon_path("logo_full")

        if logo_path:
            try:
                # Add logo image
                logo = Image(logo_path)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.2 * inch))
            except:
                # Fall back to text if image fails
                logo_text = Paragraph(
                    "<b>DELEUM OILFIELD SERVICES SDN BHD</b><br/><font size='8'>SLICKLINE WELL SERVICES</font>",
                    ParagraphStyle(name='Logo',
                                   fontSize=18,
                                   textColor=colors.HexColor('#1976D2'),
                                   alignment=TA_CENTER))
                elements.append(logo_text)
                elements.append(Spacer(1, 0.5 * inch))
        else:
            # Use text logo if no image found
            logo_text = Paragraph(
                "<b>DELEUM OILFIELD SERVICES SDN BHD</b><br/><font size='8'>SLICKLINE WELL SERVICES</font>",
                ParagraphStyle(name='Logo',
                               fontSize=18,
                               textColor=colors.HexColor('#1976D2'),
                               alignment=TA_CENTER))
            elements.append(logo_text)
            elements.append(Spacer(1, 0.5 * inch))

        # Title
        elements.append(Paragraph("TOOL LIFT FORCE ANALYSIS REPORT", self.styles['MyTitle']))
        elements.append(Spacer(1, 0.2 * inch))

        # Subtitle
        date_str = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Generated: {date_str}", self.styles['ReportSubtitle']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Comprehensive Analysis of Wireline Tool Forces", self.styles['ReportSubtitle']))

        elements.append(Spacer(1, 1 * inch))

        # Summary box with user-provided information
        client = self.report_info.get('client', 'Not Specified')
        well_number = self.report_info.get('well_number', 'Not Specified')
        prepared_by = self.report_info.get('prepared_by', 'Tool Lift Analysis Software')

        summary_data = [
            ["REPORT SUMMARY", ""],
            ["Client:", client],
            ["Well Number:", well_number],
            ["Analysis Date:", date_str],
            ["Prepared By:", prepared_by]
        ]

        summary_table = Table(summary_data, colWidths=[2 * inch, 3 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Add page break - Executive Summary will start on next page
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("<pagebreak/>", self.styles['Normal']))

        # Executive Summary (starts on page 2)
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['ReportSectionHeader']))

        # Calculate some key metrics for the summary
        net_force = self.results.get('E23', 0)
        safety_margin = abs(net_force)

        if net_force > 0:
            summary_conclusion = "The analysis indicates a NET DOWNWARD FORCE, meaning the tool will naturally descend under the specified conditions."
            risk_level = "LOW - Tool is properly weighted"
        else:
            summary_conclusion = "The analysis indicates a NET UPWARD FORCE, meaning there is a RISK OF TOOL LIFT under the specified conditions."
            risk_level = "HIGH - Risk of tool lifting from well"

        exec_summary = f"""
        This report presents a comprehensive analysis of tool lift forces for wireline operations in Well {well_number}. 
        The calculations consider fluid properties, well geometry, and tool specifications to determine the net forces 
        acting on both the wireline and tool string.

        <b>Key Findings:</b>
        • Net System Force: <b>{net_force:.0f} lbs</b> ({'Downward' if net_force > 0 else 'Upward'})
        • Safety Margin: <b>{safety_margin:.0f} lbs</b>
        • Risk Assessment: <b>{risk_level}</b>

        {summary_conclusion}

        <b>Recommendation:</b>
        {'Normal wireline operations can proceed with standard safety precautions.' if net_force > 0
        else 'Special precautions are required to prevent tool lift. Consider reducing production rates or increasing tool weight.'}
        """

        elements.append(Paragraph(exec_summary, self.styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))

    def create_input_section(self, elements):
        elements.append(PageBreak())
        elements.append(Paragraph("1. INPUT PARAMETERS", self.styles['ReportSectionHeader']))

        # Fluid Properties Table
        elements.append(Paragraph("1.1 Fluid & Flow Properties", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=8
        )))

        fluid_data = [
            ["Parameter", "Value", "Units", "Description"],
            ["Surface Pressure", f"{self.inputs.get('D6', 0):.2f}", "psia", "Wellhead pressure"],
            ["Surface Gas Flow", f"{self.inputs.get('D14', 0):.0f}", "mscfd", "Gas flow rate"],
            ["Surface Oil Flow", f"{self.inputs.get('D15', 0):.0f}", "bopd", "Oil production rate"],
            ["Surface Water Flow", f"{self.inputs.get('D16', 0):.0f}", "bwpd", "Water production rate"],
            ["Oil Solution GOR", f"{self.inputs.get('D17', 0):.0f}", "scf/bbl", "Gas-oil ratio at Pwf"],
            ["Formation Volume Factor", f"{self.inputs.get('D18', 0):.3f}", "RB/STB", "Oil formation factor"]
        ]

        fluid_table = Table(fluid_data, colWidths=[2.2 * inch, 1 * inch, 1 * inch, 2.2 * inch])
        fluid_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))

        elements.append(fluid_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Well Geometry Table
        elements.append(Paragraph("1.2 Well Geometry", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=8
        )))

        well_data = [
            ["Parameter", "Value", "Units", "Description"],
            ["Well Deviation", f"{self.inputs.get('H6', 0):.1f}", "degrees", "Angle from vertical"],
            ["Tubing ID", f"{self.inputs.get('H7', 0):.3f}", "inches", "Tubing inner diameter"],
            ["Casing ID", f"{self.inputs.get('H8', 0):.3f}", "inches", "Casing inner diameter"],
            ["Tubing Depth", f"{self.inputs.get('H12', 0):.0f}", "ft", "Depth of tubing shoe"]
        ]

        well_table = Table(well_data, colWidths=[2.2 * inch, 1 * inch, 1 * inch, 2.2 * inch])
        well_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(well_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Tool & Wire Geometry Table
        elements.append(Paragraph("1.3 Tool & Wire Geometry", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=8
        )))

        tool_data = [
            ["Parameter", "Value", "Units", "Description"],
            ["Tool OD", f"{self.inputs.get('H9', 0):.3f}", "inches", "Tool outer diameter"],
            ["Tool Length", f"{self.inputs.get('H10', 0):.1f}", "ft", "Length of tool string"],
            ["Wireline OD", f"{self.inputs.get('H11', 0):.3f}", "inches", "Wireline diameter"],
            ["Tool Depth", f"{self.inputs.get('H13', 0):.0f}", "ft", "Toolstring depth"],
            ["Line Weight", f"{self.inputs.get('H14', 0):.1f}", "lbs/1000ft", "Wireline weight in air"],
            ["Tool Weight", f"{self.inputs.get('H15', 0):.1f}", "lbs", "Toolstring weight in air"]
        ]

        tool_table = Table(tool_data, colWidths=[2.2 * inch, 1 * inch, 1 * inch, 2.2 * inch])
        tool_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(tool_table)

        elements.append(Spacer(1, 0.5 * inch))

    def create_results_section(self, elements):
        elements.append(PageBreak())
        elements.append(Paragraph("2. CALCULATION RESULTS", self.styles['ReportSectionHeader']))

        # Positive Forces Table
        elements.append(Paragraph("2.1 Positive Forces (Downward)", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=8
        )))

        positive_data = [
            ["Parameter", "Value (lbs)", "Description"],
            ["Line weight less buoyancy", f"{self.results.get('E30', 0):.1f}", "Wire weight in fluid"],
            ["Tool weight less buoyancy", f"{self.results.get('E31', 0):.1f}", "Tool weight in fluid"],
            ["Total positive forces", f"{self.results.get('E32', 0):.1f}", "Sum of downward forces"]
        ]

        positive_table = Table(positive_data, colWidths=[2.5 * inch, 1.5 * inch, 2.5 * inch])
        positive_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))

        elements.append(positive_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Counter Forces Table
        elements.append(Paragraph("2.2 Counter Forces (Upward)", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#D32F2F'),
            spaceAfter=8
        )))

        counter_data = [
            ["Parameter", "Value (lbs)", "Description"],
            ["Surface pull on line", f"{self.results.get('H27', 0):.1f}", "Applied surface tension"],
            ["Wellhead pressure force", f"{self.results.get('H28', 0):.1f}", "Pressure area force"],
            ["Friction force", f"{self.results.get('H29', 0):.1f}", "Wire friction"],
            ["Lift/drag on line", f"{self.results.get('H30', 0):.1f}", f"{self.calculated_values.get('V39', '')}"],
            ["Lift/drag on tool", f"{self.results.get('H31', 0):.1f}", f"{self.calculated_values.get('V37', '')}"],
            ["Total counter forces", f"{self.results.get('H32', 0):.1f}", "Sum of upward forces"]
        ]

        counter_table = Table(counter_data, colWidths=[2.5 * inch, 1.5 * inch, 2.5 * inch])
        counter_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F44336')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))

        elements.append(counter_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Final Results - Highlighted
        elements.append(Paragraph("2.3 FINAL RESULTS - NET FORCES", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#1976D2'),
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )))

        final_data = [
            ["Result", "Net Force (lbs)", "Interpretation"],
            ["Net force on wire", f"{self.results.get('E21', 0):.0f}",
             self.interpret_force(self.results.get('E21', 0))],
            ["Net force on tool string", f"{self.results.get('E22', 0):.0f}",
             self.interpret_force(self.results.get('E22', 0))],
            ["Net force of system", f"{self.results.get('E23', 0):.0f}",
             self.interpret_force(self.results.get('E23', 0), is_system=True)]
        ]

        final_table = Table(final_data, colWidths=[2 * inch, 1.5 * inch, 3 * inch])
        final_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1976D2')),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (1, -1), 14),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#D32F2F')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))

        elements.append(final_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Additional Calculated Parameters
        elements.append(Paragraph("2.4 Additional Calculated Parameters", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=8
        )))

        calc_data = [
            ["Parameter", "Value", "Units", "Description"],
            ["Downhole Pressure", f"{self.calculated_values.get('D7', 0):.1f}", "psia", "Pressure at tool depth"],
            ["Avg Fluid Density", f"{self.calculated_values.get('D8', 0):.3f}", "g/cc", "Mixed fluid density"],
            ["Fluid Density (avg)", f"{self.calculated_values.get('Q8', 0):.3f}", "g/cc",
             "Average density in annulus"],
            ["Fluid Density (tool)", f"{self.calculated_values.get('Q17', 0):.3f}", "g/cc", "Density at tool"],
            ["Flow Rate (avg)", f"{self.calculated_values.get('N8', 0):.0f}", "ft³/min", "Average annular flow"],
            ["Flow Rate (tool)", f"{self.calculated_values.get('N17', 0):.0f}", "ft³/min", "Flow at tool depth"]
        ]

        calc_table = Table(calc_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 2.5 * inch])
        calc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#757575')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FAFAFA')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(calc_table)

        elements.append(Spacer(1, 0.5 * inch))

    def create_conclusions_section(self, elements):
        elements.append(PageBreak())
        elements.append(Paragraph("3. CONCLUSIONS & RECOMMENDATIONS", self.styles['ReportSectionHeader']))

        # Interpretation
        net_force = self.results.get('E23', 0)

        if net_force > 0:
            conclusion = "NET DOWNWARD FORCE - Tool will tend to fall"
            recommendation = """
            • Tool is under positive weight in hole
            • Normal wireline operations can proceed
            • Ensure adequate surface weight indicator capacity
            • Monitor for any changes in fluid properties
            """
            color = colors.HexColor('#2E7D32')
        else:
            conclusion = "NET UPWARD FORCE - Risk of tool lift"
            recommendation = """
            • CRITICAL: Tool may lift from upward forces
            • Consider reducing production rates during operation
            • Evaluate need for additional surface pull
            • Consider tool string weight increase
            • Monitor well parameters closely
            """
            color = colors.HexColor('#D32F2F')

        # Conclusion Box
        elements.append(Paragraph("3.1 Force Analysis Conclusion", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=color,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )))

        conclusion_text = f"""
        <b>Overall Result:</b> {conclusion}<br/>
        <b>Net System Force:</b> {net_force:.0f} lbs ({'Downward' if net_force > 0 else 'Upward'})<br/>
        <b>Safety Margin:</b> {abs(net_force):.0f} lbs
        """

        elements.append(Paragraph(conclusion_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))

        # Recommendations
        elements.append(Paragraph("3.2 Operational Recommendations", ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#FF9800'),
            spaceAfter=8
        )))

        elements.append(Paragraph(recommendation, self.styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))

        # Disclaimer
        elements.append(Paragraph("4. DISCLAIMER", self.styles['ReportSectionHeader']))
        disclaimer = f"""
        This analysis is based on the input parameters provided and standard engineering calculations. 
        Actual field conditions may vary. This report is for planning purposes only and should be 
        used in conjunction with field experience and operational judgment. Always follow safe 
        operating procedures and manufacturer guidelines.

        <b>Report Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")} by Tool Lift Analysis Software v1.0
        <b>Prepared For:</b> {self.report_info.get('client', 'Not Specified')}
        <b>Well:</b> {self.report_info.get('well_number', 'Not Specified')}
        <b>Prepared By:</b> {self.report_info.get('prepared_by', 'Tool Lift Analysis Software')}
        """

        elements.append(Paragraph(disclaimer, ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_JUSTIFY,
            borderPadding=10,
            borderColor=colors.grey,
            borderWidth=1,
            borderRadius=5,
            backgroundColor=colors.HexColor('#FAFAFA')
        )))

    def interpret_force(self, force, is_system=False):
        if is_system:
            if force > 100:
                return "Significant downward force - tool will descend"
            elif force > 0:
                return "Slight downward force - tool is weighted"
            elif force > -100:
                return "Slight upward force - monitor conditions"
            else:
                return "Significant upward force - risk of tool lift"
        else:
            if force > 0:
                return "Net downward force"
            else:
                return "Net upward force"

    def generate_report(self, filename):
        # Create PDF document
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            topMargin=1.5 * inch,
            bottomMargin=1 * inch,
            leftMargin=inch,
            rightMargin=inch
        )

        # Create story (elements to add to PDF)
        elements = []

        # Add title page (with logo and basic info, executive summary on next page)
        self.create_title_page(elements)

        # Add input section
        self.create_input_section(elements)

        # Add results section
        self.create_results_section(elements)

        # Add conclusions section
        self.create_conclusions_section(elements)

        # Build PDF with header/footer
        doc.build(elements, onFirstPage=self.header_footer, onLaterPages=self.header_footer)

        return True


MSGBOX_BLACK_TEXT_STYLE = """
QMessageBox {
    color: black;
    background-color: white;
    font-size: 12px;
}
QLabel {
    color: black;
}
QPushButton {
    color: black;
    background-color: #f0f0f0;
    padding: 6px 12px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #e0e0e0;
}
"""


# =========================
# REDESIGNED PYQT UI WITH INFORMATIVE LABELS
# =========================
class ToolLiftTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool Lift Calculator")
        self.resize(1200, 800)
        self.current_model = None
        self.init_ui()

    def init_ui(self):

        GROUPBOX_WHITE_STYLE = """
        QGroupBox {
            font-weight: bold;
            color: white;
            border: 2px solid white;
            border-radius: 6px;
            margin-top: 14px;
            background: transparent;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }
        """

        GROUPBOX_GREEN_STYLE = """
        QGroupBox {
            font-weight: bold;
            color: #4CAF50;
            border: 2px solid #4CAF50;
            border-radius: 6px;
            margin-top: 14px;
            background: transparent;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }
        """

        LABEL_WHITE_STYLE = "color: white; font-weight: bold; background: transparent;"

        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Tool Lift Force Calculator")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: white; background: transparent;")
        main_layout.addWidget(title_label)

        # Create horizontal layout for input groups
        input_layout = QHBoxLayout()

        # D Column Inputs Group
        d_group = QGroupBox("Fluid & Flow Properties")
        d_layout = QGridLayout()

        # Well Geometry Group (from H column)
        well_group = QGroupBox("Well Geometry")
        well_layout = QGridLayout()

        # Tool/Wire Geometry Group (from H column)
        tool_group = QGroupBox("Tool & Wire Geometry")
        tool_layout = QGridLayout()

        # Cell information dictionary (name, unit, group)
        cell_info = {
            "D6": ("Surface pressure", "psia", "fluid"),
            "D14": ("Surface gas flowrate", "mscfd", "fluid"),
            "D15": ("Surface oil flowrate", "bopd", "fluid"),
            "D16": ("Surface water flowrate", "bwpd", "fluid"),
            "D17": ("Oil Solution GOR at Pwf", "scf/bbl", "fluid"),
            "D18": ("Formation Volume Factor (Bo)", "RB/STB", "fluid"),

            "H6": ("Well Deviation", "degrees", "well"),
            "H7": ("Tubing ID", "inches", "well"),
            "H8": ("Casing ID", "inches", "well"),
            "H12": ("Tubing Depth", "ft", "well"),

            "H9": ("Tool OD", "inches", "tool"),
            "H10": ("Tool Length", "ft", "tool"),
            "H11": ("Wireline OD", "inches", "tool"),
            "H13": ("Toolstring Depth", "ft", "tool"),
            "H14": ("Line Weight/1000ft (air)", "lbs", "tool"),
            "H15": ("Toolstring Weight (air)", "lbs", "tool")
        }

        self.inputs = {}
        self.outputs = {}

        # Add D column inputs (fluid properties)
        d_cells = ["D6", "D14", "D15", "D16", "D17", "D18"]
        for i, cell in enumerate(d_cells):
            name, unit, _ = cell_info[cell]
            label = QLabel(f"{name} ({unit})")
            label.setStyleSheet(LABEL_WHITE_STYLE)

            d_layout.addWidget(label, i, 0)
            le = QLineEdit()
            le.setPlaceholderText(f"Enter {name}")
            le.setStyleSheet("""
                QLineEdit {
                    color: black;
                    background-color: white;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                QLineEdit:focus {
                    border: 2px solid #4CAF50;
                }
            """)
            self.inputs[cell] = le
            d_layout.addWidget(le, i, 1)

        d_group.setLayout(d_layout)

        # Add Well Geometry inputs
        well_cells = ["H6", "H7", "H8", "H12"]
        for i, cell in enumerate(well_cells):
            name, unit, _ = cell_info[cell]
            label = QLabel(f"{name} ({unit})")
            label.setStyleSheet(LABEL_WHITE_STYLE)

            well_layout.addWidget(label, i, 0)
            le = QLineEdit()
            le.setPlaceholderText(f"Enter {name}")
            le.setStyleSheet("""
                QLineEdit {
                    color: black;
                    background-color: white;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                QLineEdit:focus {
                    border: 2px solid #2196F3;
                }
            """)
            self.inputs[cell] = le
            well_layout.addWidget(le, i, 1)

        well_group.setLayout(well_layout)

        # Add Tool/Wire Geometry inputs
        tool_cells = ["H9", "H10", "H11", "H13", "H14", "H15"]
        for i, cell in enumerate(tool_cells):
            name, unit, _ = cell_info[cell]
            label = QLabel(f"{name} ({unit})")
            label.setStyleSheet(LABEL_WHITE_STYLE)

            tool_layout.addWidget(label, i, 0)
            le = QLineEdit()
            le.setPlaceholderText(f"Enter {name}")
            le.setStyleSheet("""
                QLineEdit {
                    color: black;
                    background-color: white;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                QLineEdit:focus {
                    border: 2px solid #FF9800;
                }
            """)
            self.inputs[cell] = le
            tool_layout.addWidget(le, i, 1)

        tool_group.setLayout(tool_layout)

        # Add input groups to horizontal layout with appropriate stretch factors
        input_layout.addWidget(d_group, 2)  # Fluid group
        input_layout.addWidget(well_group, 1)  # Well geometry group
        input_layout.addWidget(tool_group, 2)  # Tool/wire geometry group

        main_layout.addLayout(input_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Create results section with multiple groups
        results_layout = QHBoxLayout()

        # Positive Forces Group
        positive_group = QGroupBox("Positive Forces (Downward)")
        positive_layout = QGridLayout()

        # Counter Forces Group
        counter_group = QGroupBox("Counter Forces (Upward)")
        counter_layout = QGridLayout()

        # Final Results Group (highlighted)
        final_group = QGroupBox("Final Results")
        final_group.setStyleSheet(GROUPBOX_GREEN_STYLE)
        final_layout = QGridLayout()

        # Positive Forces (E30, E31, E32)
        positive_labels = {
            "E30": "Line weight deviated less buoyancy",
            "E31": "Tool string weight deviated less buoyancy",
            "E32": "Total positive (downward) forces"
        }

        row = 0
        for cell in ["E30", "E31", "E32"]:
            label = QLabel(f"{positive_labels[cell]}")
            label.setStyleSheet(LABEL_WHITE_STYLE)

            positive_layout.addWidget(label, row, 0)
            lbl = QLabel("-")
            lbl.setStyleSheet("""
                font-weight: bold; 
                padding: 5px;
                color: black;
                background-color: #E8F5E9;
                border: 1px solid #C8E6C9;
                border-radius: 4px;
                min-width: 100px;
            """)
            lbl.setMinimumWidth(100)
            self.outputs[cell] = lbl
            positive_layout.addWidget(lbl, row, 1)
            row += 1

        positive_group.setLayout(positive_layout)

        # Counter Forces (H27 to H32)
        counter_labels = {
            "H27": "Surface pull on line",
            "H28": "Wellhead press",
            "H29": "Press control friction",
            "H30": "Lift/drag on line",
            "H31": "Lift/drag on tool string",
            "H32": "Total counter forces"
        }

        row = 0
        for cell in ["H27", "H28", "H29", "H30", "H31", "H32"]:
            label = QLabel(f"{counter_labels[cell]}")
            label.setStyleSheet(LABEL_WHITE_STYLE)

            counter_layout.addWidget(label, row, 0)
            lbl = QLabel("-")
            lbl.setStyleSheet("""
                font-weight: bold; 
                padding: 5px;
                color: black;
                background-color: #FFEBEE;
                border: 1px solid #FFCDD2;
                border-radius: 4px;
                min-width: 100px;
            """)
            lbl.setMinimumWidth(100)
            self.outputs[cell] = lbl
            counter_layout.addWidget(lbl, row, 1)
            row += 1

        counter_group.setLayout(counter_layout)

        # Final Results (E21, E22, E23) - Highlighted
        final_labels = {
            "E21": "Net force on the wire (lbs)",
            "E22": "Net force on the tool string (lbs)",
            "E23": "Net force of system (lbs)"
        }

        row = 0
        for cell in ["E21", "E22", "E23"]:
            # Label with description
            label = QLabel(f"{final_labels[cell]}")
            label.setStyleSheet("color: white; font-weight: bold; font-size: 13px; background: transparent;")

            final_layout.addWidget(label, row, 0)

            # Value display
            lbl = QLabel("-")
            lbl.setStyleSheet("""
                font-weight: bold; 
                font-size: 14px; 
                padding: 10px;
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                color: black;
                min-width: 120px;
            """)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.outputs[cell] = lbl
            final_layout.addWidget(lbl, row, 1)

            row += 1

        final_group.setLayout(final_layout)

        # Add groups to results layout
        results_layout.addWidget(positive_group, 1)
        results_layout.addWidget(counter_group, 1)
        results_layout.addWidget(final_group, 1)

        main_layout.addLayout(results_layout)

        # Button layout for Calculate, Fill Test Values, and Generate Report
        button_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 16px;
                border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_inputs)
        button_layout.addWidget(clear_btn)

        # Calculate button
        calc_btn = QPushButton("Calculate Tool Lift Forces")
        calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 16px;
                border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        calc_btn.clicked.connect(self.calculate)
        button_layout.addWidget(calc_btn)

        # Generate Report button
        report_btn = QPushButton("Generate PDF Report")
        report_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 16px;
                border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        report_btn.clicked.connect(self.generate_pdf_report)
        report_btn.setEnabled(False)  # Disabled until calculation is done
        self.report_btn = report_btn
        button_layout.addWidget(report_btn)

        main_layout.addLayout(button_layout)

        # Formula/Notes section
        notes_group = QGroupBox("Notes & Fixed Parameters")
        notes_layout = QVBoxLayout()

        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(120)
        notes_text.setStyleSheet("""
            QTextEdit {
                color: black;
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 3px;
                padding: 5px;
                font-family: 'Courier New';
            }
        """)

        notes_content = """
        Fixed Parameters (not editable):
        • D9 (Downhole water density): 0.96 g/cc
        • D10 (Surface Oil API): 41.1 °API
        • D11 (Downhole Temperature): 237 °F
        • D13 (Gas Specific Gravity): 0.800 (Air=1)
        • H16 (Wire friction): 25 lbs
        • H17 (Line Friction Factor): 0.0035
        • H18 (Surface pull on line): 20 lbs

        Results Interpretation:
        • E21: Force required at surface to hold/lift wire
        • E22: Force required at surface to hold/lift tool string
        • E23: Total force required at surface
        • Positive values = downward force, Negative values = upward force
        """

        notes_text.setText(notes_content)
        notes_layout.addWidget(notes_text)
        notes_group.setLayout(notes_layout)

        # main_layout.addWidget(notes_group)

        d_group.setStyleSheet(GROUPBOX_WHITE_STYLE)
        well_group.setStyleSheet(GROUPBOX_WHITE_STYLE)
        tool_group.setStyleSheet(GROUPBOX_WHITE_STYLE)

        positive_group.setStyleSheet(GROUPBOX_WHITE_STYLE)
        counter_group.setStyleSheet(GROUPBOX_WHITE_STYLE)

        notes_group.setStyleSheet(GROUPBOX_WHITE_STYLE)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }

            QLabel {
                color: white;
                background: transparent;
            }
        """)

        # Fill with test values automatically when UI loads
        self.fill_test_values()

    def fill_test_values(self):
        """Fill input fields with test values for debugging"""
        test_values = {
            "D6": "200",  # Surface pressure (psia)
            "D14": "809",  # Surface gas flowrate (mscfd)
            "D15": "159",  # Surface oil flowrate (bopd)
            "D16": "2119",  # Surface water flowrate (bwpd)
            "D17": "1560",  # Oil Solution GOR at Pwf (scf/bbl)
            "D18": "1.322",  # Formation Volume Factor (Bo) (RB/STB)

            "H6": "69",  # Well Deviation (degrees)
            "H7": "2.992",  # Tubing ID (inches)
            "H8": "6.184",  # Casing ID (inches)
            "H12": "6996",  # Tubing Depth (ft)

            "H9": "1.5",  # Tool OD (inches)
            "H10": "20.3",  # Tool Length (ft)
            "H11": "0.125",  # Wireline OD (inches)
            "H13": "7029",  # Toolstring Depth (ft)
            "H14": "41.7",  # Line Weight/1000ft (air) (lbs)
            "H15": "109.9"  # Toolstring Weight (air) (lbs)
        }

        # Fill each input field
        for cell, value in test_values.items():
            if cell in self.inputs:
                self.inputs[cell].setText(value)

        # Show status message
        self.show_status("Test values filled. Click 'Calculate' to run.")

    def clear_all_inputs(self):
        """Clear all input fields and reset outputs"""
        for widget in self.inputs.values():
            widget.clear()
            widget.setStyleSheet("""
                QLineEdit {
                    color: black;
                    background-color: white;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                }
            """)

        for lbl in self.outputs.values():
            lbl.setText("-")

        self.current_model = None
        self.report_btn.setEnabled(False)

        self.show_status("All inputs and results cleared.")

    def calculate(self):
        try:
            # Collect input values
            values = {}
            for cell, widget in self.inputs.items():
                text = widget.text().strip()
                if text:
                    values[cell] = float(text)
                else:
                    # Show error for empty required fields
                    widget.setStyleSheet("""
                        QLineEdit {
                            color: black;
                            background-color: white;
                            border: 2px solid #F44336;
                            padding: 5px;
                            border-radius: 3px;
                        }
                    """)
                    self.show_error(f"Please enter value for {cell}")
                    return
                widget.setStyleSheet("""
                    QLineEdit {
                        color: black;
                        background-color: white;
                        border: 1px solid #cccccc;
                        padding: 5px;
                        border-radius: 3px;
                    }
                """)  # Reset style

            # Create model and calculate
            self.current_model = ToolLiftModel(values)

            # Update output labels
            for cell in self.outputs:
                if hasattr(self.current_model, cell):
                    value = getattr(self.current_model, cell)
                    # Format with 1 decimal place for intermediate results, 0 for final
                    if cell in ["E21", "E22", "E23"]:
                        self.outputs[cell].setText(f"{value:.0f}")
                    else:
                        self.outputs[cell].setText(f"{value:.1f}")

            # Enable report button
            self.report_btn.setEnabled(True)

            # Display success message
            self.show_status("Calculation completed successfully! You can now generate a PDF report.")

        except ValueError as e:
            self.show_error(f"Invalid input format: {str(e)}")
        except Exception as e:
            self.show_error(f"Calculation error: {str(e)}")

    def generate_pdf_report(self):
        if not self.current_model:
            QMessageBox.warning(self, "No Data", "Please calculate first before generating a report.")
            return

        try:
            # Prompt user for report information
            dialog = ReportInfoDialog(self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return  # User cancelled

            report_info = dialog.get_info()

            # Validate required fields
            if not report_info['client'] or not report_info['well_number'] or not report_info['prepared_by']:
                QMessageBox.warning(self, "Missing Information",
                                    "Please fill in all fields: Client, Well Number, and Prepared By.")
                return

            # Get file location for saving
            well_number = report_info['well_number'].replace(' ', '_').replace('/', '_')
            default_filename = f"Tool_Lift_Report_{well_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save PDF Report",
                default_filename,
                "PDF Files (*.pdf);;All Files (*)"
            )

            if not file_path:
                return  # User cancelled

            # Ensure .pdf extension
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'

            # Prepare data for report
            inputs = {}
            for cell, widget in self.inputs.items():
                try:
                    inputs[cell] = float(widget.text())
                except:
                    inputs[cell] = 0.0

            results = {}
            for cell in self.outputs:
                if hasattr(self.current_model, cell):
                    results[cell] = getattr(self.current_model, cell)

            calculated_values = getattr(self.current_model, 'calculated_values', {})

            # Generate report
            report_gen = PDFReportGenerator(inputs, results, calculated_values, report_info)
            success = report_gen.generate_report(file_path)

            if success:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Report Generated")
                msg.setText(
                    f"PDF report has been successfully generated:\n\n{file_path}\n\n"
                    f"Client: {report_info['client']}\n"
                    f"Well: {report_info['well_number']}\n"
                    f"Prepared By: {report_info['prepared_by']}"
                )
                msg.setStyleSheet(MSGBOX_BLACK_TEXT_STYLE)
                msg.exec()

                # Optionally open the PDF
                open_msg = QMessageBox(self)
                open_msg.setIcon(QMessageBox.Icon.Question)
                open_msg.setWindowTitle("Open Report")
                open_msg.setText("Would you like to open the generated PDF report?")
                open_msg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                open_msg.setStyleSheet(MSGBOX_BLACK_TEXT_STYLE)

                open_pdf = open_msg.exec()

                if open_pdf == QMessageBox.StandardButton.Yes:
                    if sys.platform == "win32":
                        os.startfile(file_path)
                    elif sys.platform == "darwin":  # macOS
                        os.system(f"open '{file_path}'")
                    else:  # Linux
                        os.system(f"xdg-open '{file_path}'")

        except Exception as e:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("Report Generation Failed")
            error_msg.setText(f"Failed to generate PDF report:\n\n{str(e)}")
            error_msg.setStyleSheet(MSGBOX_BLACK_TEXT_STYLE)
            error_msg.exec()

    def show_error(self, message):
        # Create a messagebox with black text
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: black;
            }
            QPushButton {
                color: black;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        msg_box.exec()

    def show_status(self, message):
        # Could be enhanced with a status bar
        print(f"STATUS: {message}")