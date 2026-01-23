import math

from PyQt6.QtCore import Qt, QPointF, QTimer, QRectF
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, \
    QHBoxLayout, QApplication, QSplitter, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, \
    QDialog, QScrollArea
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush, QPolygonF, QPixmap, QImage, QPainterPath
import pandas as pd

from utils.path_finder import get_tool_image_path


class WirefallTab(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.df = pd.DataFrame(data, columns=["Tubing O.D.", "Wire Size", "Wire Fall/1000'"])
        self.init_ui()

    def init_ui(self):
        # Create a main layout
        main_layout = QVBoxLayout(self)

        # Create a horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side container (input + illustration)
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)

        # Input section
        input_widget = QWidget()
        input_widget.setLayout(self.create_input_section())
        left_layout.addWidget(input_widget, stretch=2)

        # Illustration
        self.wire_illustration = WireIllustration()

        # Add copy button to illustration
        self.copy_illustration_btn = QPushButton("Copy Illustration")
        self.copy_illustration_btn.clicked.connect(self.copy_illustration_to_clipboard)
        self.copy_illustration_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
                padding: 5px;
                border-radius: 4px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)

        # Add button below the illustration
        illustration_container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.wire_illustration)
        container_layout.addWidget(self.copy_illustration_btn)
        illustration_container.setLayout(container_layout)

        # Replace in left_layout:
        left_layout.addWidget(illustration_container, stretch=1)

        # Right side (formula)
        formula_widget = QWidget()
        formula_widget.setLayout(self.create_formula_section())

        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(formula_widget)

        # Set initial sizes
        splitter.setSizes([500, 400])

        # Add splitter to main layout
        main_layout.addWidget(splitter)

    def create_input_section(self):
        layout = QGridLayout()

        row = 0

        # Reference image button
        self.reference_btn = QPushButton("Reference")
        self.reference_btn.setFixedWidth(90)
        self.reference_btn.clicked.connect(self.show_reference_image)
        self.reference_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reference_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 4px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        layout.addWidget(self.reference_btn, row+1, 2)
        #reference button

        # A – Depth of Tool String
        layout.addWidget(QLabel("Depth of End of Tool String (A):"), row, 0)
        self.input_A = QLineEdit()
        layout.addWidget(self.input_A, row, 1)

        self.unit_toggle_btn = QPushButton("Units: ft")
        self.unit_toggle_btn.setCheckable(True)
        self.unit_toggle_btn.clicked.connect(self.toggle_units)
        layout.addWidget(self.unit_toggle_btn, row, 2)
        row += 1

        # B – Odometer reading
        layout.addWidget(QLabel("Odometer Reading (Wire into Drum) (B):"), row, 0)
        self.input_B = QLineEdit()
        layout.addWidget(self.input_B, row, 1)
        row += 1

        # D – S/B to wireline deck
        layout.addWidget(QLabel("S/B to Wireline Deck (D):"), row, 0)
        self.input_D = QLineEdit()
        layout.addWidget(self.input_D, row, 1)
        row += 1

        # E – RSU to hay pulley
        layout.addWidget(QLabel("RSU to Hay Pulley (E):"), row, 0)
        self.input_E = QLineEdit()
        layout.addWidget(self.input_E, row, 1)
        row += 1

        # F – Length of tool string
        layout.addWidget(QLabel("Length of tool string (F):"), row, 0)
        self.input_F = QLineEdit()
        layout.addWidget(self.input_F, row, 1)
        row += 1

        # H – Length from S/B to zero point
        layout.addWidget(QLabel("Length from S/B to zero point (H):"), row, 0)
        self.input_H = QLineEdit()
        layout.addWidget(self.input_H, row, 1)
        row += 1

        # Wire & Tubing selection
        layout.addWidget(QLabel("Wire Size:"), row, 0)
        self.wire_combo = QComboBox()
        self.wire_combo.addItems(sorted(self.df["Wire Size"].unique()))
        layout.addWidget(self.wire_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Tubing O.D.:"), row, 0)
        self.tubing_combo = QComboBox()
        self.tubing_combo.addItems(sorted(self.df["Tubing O.D."].unique()))
        layout.addWidget(self.tubing_combo, row, 1)
        row += 1

        # Calculate button
        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.clicked.connect(self.calculate_wirefall)
        self.calculate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)
        layout.addWidget(self.calculate_btn, row, 0, 1, 3)
        row += 1

        # Outputs
        self.output_G1 = QLabel("Wire Fall Back per 1000': -")
        self.output_G2 = QLabel("Wire Fall Back Total: -")
        self.output_W1 = QLabel("Wire Left in Hole (W1): -")
        self.output_W2 = QLabel("Top of Wire (W2): -")

        layout.addWidget(self.output_G1, row, 0, 1, 3)
        row += 1
        layout.addWidget(self.output_G2, row, 0, 1, 3)
        row += 1
        layout.addWidget(self.output_W1, row, 0, 1, 3)
        row += 1
        layout.addWidget(self.output_W2, row, 0, 1, 3)

        return layout

    def show_reference_image(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Wirefall Reference")
        dialog.resize(600, 800)

        layout = QVBoxLayout(dialog)

        # Scroll area (important for large images)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load reference image
        image_path = get_tool_image_path("Wirefall Reference")  # adjust key as needed
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            image_label.setText("Reference image not found.")
        else:
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)

        scroll_area.setWidget(image_label)
        layout.addWidget(scroll_area)

        dialog.exec()

    def create_formula_section(self):
        formula_layout = QVBoxLayout()

        self.formula_display = QTextEdit()
        self.formula_display.setReadOnly(True)
        self.formula_display.setFont(QFont("Cambria Math", 10))


        self.formula_document = self.formula_display.document()
        self.formula_document.setDefaultStyleSheet("""
            body { 
                font-family: 'Cambria Math', 'Times New Roman', serif;
                font-size: 12pt;
            }
        """)

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_formula)

        formula_layout.addWidget(QLabel("\nCalculation Breakdown:"))
        formula_layout.addWidget(self.formula_display)
        formula_layout.addWidget(copy_button)

        return formula_layout


    def toggle_units(self):
        if self.unit_toggle_btn.isChecked():
            self.unit_toggle_btn.setText("Units: m")
        else:
            self.unit_toggle_btn.setText("Units: ft")

    def calculate_wirefall(self):
        try:
            A = float(self.input_A.text())
            B = float(self.input_B.text())
            D = float(self.input_D.text())
            E = float(self.input_E.text())
            F = float(self.input_F.text())
            H = float(self.input_H.text())

            C = H - F

            tubing = self.tubing_combo.currentText()
            wire = self.wire_combo.currentText()

            row = self.df[(self.df["Tubing O.D."] == tubing) & (self.df["Wire Size"] == wire)]
            if row.empty:
                self.formula_display.setHtml("<div style='color: red;'>No data for this combination.</div>")
                return

            G1 =  row.iloc[0]["Wire Fall/1000'"]
            W1 = B + C + D + E
            G2 = (G1 / 1000) * W1
            A2 = A - F
            W2 = A2 - (W1 - G2)

            self.output_G1.setText(f"Wire Fall Back per 1000': {G1} ft")
            self.output_G2.setText(f"Wire Fall Back Total: {G2:.2f} ft")
            self.output_W1.setText(f"Wire left in hole (Approximate): {W1:.2f} ft")
            self.output_W2.setText(f"Top of Wire (Approximate): {W2:.2f} ft")

            # Update the wire illustration
            self.wire_illustration.update_illustration(A2, W1, W2, G2)

            self.formula_display.setHtml(f"""
                <style>                    
                    .formula {{ 
                        font-family: 'Cambria Math', 'Times New Roman', serif;
                        font-size: 12pt;
                        margin: 5px 0;
                    }}
                    .result {{
                        font-weight: bold;
                        color: #800020;
                        margin: 10px 0 15px 0;
                        font-size: 14pt;
                    }}
                    .frac {{
                        display: inline-block;
                        vertical-align: middle; 
                        text-align: center;
                    }}
                    .numerator {{
                        padding: 0 5px;    
                    }}
                    .denominator {{
                        border-top: 1px solid;
                        padding: 0 5px;
                    }}
                    .unit {{
                        font-style: italic;
                    }}
                </style>

                <div class="result">Wire Left in Hole (Approximate)</div>
                <div class="formula"><i>W1</i> = {B:.2f} + {C:.2f} + {D:.2f} + {E:.2f}</div>
                <div class="formula">= {W1:.2f} <span class="unit">ft</span></div>
                
                <div class="result">Wire Fall Back Total</div>
                <div class="formula">
                    <i>G</i><sub>total</sub> = 
                    <span class="frac">
                        <span class="numerator">{G1}</span>
                        <span class="denominator">/1000</span>
                    </span>
                    × {W1:.2f}
                </div>
                <div class="formula">= {G2:.2f} <span class="unit">ft</span></div>

                <div class="result">Top of Wire (Approximate)</div>
                <div class="formula"><i>W2</i> = {A2:.2f} − ({W1:.2f} - {G2:.2f})</div>
                <div class="formula">= {W2:.2f} <span class="unit">ft</span></div>
            """)

        except ValueError:
            self.formula_display.setHtml("<div style='color: red;'>Please enter valid numeric inputs.</div>")

    def copy_formula(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.formula_display.toPlainText())

    def copy_illustration_to_clipboard(self):
        # First test with simple text to verify clipboard works
        clipboard = QApplication.clipboard()
        clipboard.setText("TEST - Clipboard is working")
        print("Clipboard test executed")  # Verify this prints in your console

        # Now try copying the image
        if self.wire_illustration.copy_to_clipboard():
            print("Image copied successfully")
            self.show_copy_confirmation()
        else:
            print("Failed to copy image")
            self.copy_illustration_btn.setToolTip("Failed to copy image")

    def show_copy_confirmation(self):
        # Show a temporary message
        self.copy_illustration_btn.setText("Copied!")
        self.copy_illustration_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
            }
        """)

        # Reset after 2 seconds
        QTimer.singleShot(2000, self.reset_copy_button)

    def reset_copy_button(self):
        self.copy_illustration_btn.setText("Copy Illustration")
        self.copy_illustration_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)

class WireIllustration(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        # Initialize with default values
        self.depth = 0
        self.wire_left = 0
        self.top_wire = 0
        self.total_fall = 0
        self.max_depth = 5000

        # Set a fixed scene rectangle
        self.scene.setSceneRect(0, 0, 300, self.max_depth)

        # Draw initial empty well
        self.rope_socket_img = None
        self.load_rope_socket_image()
        self.draw_empty_well()

    def load_rope_socket_image(self):
        try:
            # Try loading from file first
            self.rope_socket_img = QPixmap(get_tool_image_path('Rope Socket'))
            if self.rope_socket_img.isNull():
                # If file not found, create a simple placeholder
                img = QImage(30, 50, QImage.Format.Format_ARGB32)
                img.fill(Qt.GlobalColor.transparent)

                # Draw a simple rope socket shape
                painter = QPainter(img)
                painter.setPen(QPen(Qt.GlobalColor.darkGray, 2))
                painter.setBrush(QBrush(QColor(100, 100, 100)))
                painter.drawRect(5, 5, 20, 40)  # Main body
                painter.drawEllipse(10, 0, 10, 10)  # Top eye
                painter.end()

                self.rope_socket_img = QPixmap.fromImage(img)
        except:
            # Fallback to a colored rectangle if all else fails
            self.rope_socket_img = None

    def draw_empty_well(self):
        self.scene.clear()
        well_width = 70

        # Calculate visible area with default max_depth
        view_rect = self.viewport().rect()
        visible_height = view_rect.height()
        scale_factor = visible_height / self.max_depth

        # Adjust scene rectangle
        self.scene.setSceneRect(0, 0, well_width + 150, self.max_depth * scale_factor)

        # Draw well casing (scaled)
        casing = QGraphicsRectItem(0, 0, well_width, self.max_depth * scale_factor * 1.5)
        casing.setPen(QPen(Qt.GlobalColor.gray, 2))
        casing.setBrush(QColor(240, 240, 240))
        self.scene.addItem(casing)

        # Draw tubing (scaled)
        tubing_width = well_width - 20
        tubing = QGraphicsRectItem(10, 0, tubing_width, self.max_depth * scale_factor * 1.5)
        tubing.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        tubing.setBrush(Qt.GlobalColor.transparent)
        self.scene.addItem(tubing)

        # Draw rope socket at bottom (scaled)
        socket_height = 25 * scale_factor
        socket_width = 30 * scale_factor
        socket_y = (self.max_depth * scale_factor * 0.7) - socket_height
        # Position so top of image touches bottom of wire
        socket = self.scene.addPixmap(self.rope_socket_img)
        socket.setPos(
            well_width / 2 - self.rope_socket_img.width() / 2,  # Center horizontally
            socket_y  # Position top of image at socket depth
        )
        socket.setZValue(10)  # Make sure it's on top


        # Draw straight wire from socket to top (scaled)
        wire_pen = QPen(QColor(139, 69, 19), 2 * scale_factor * 0.7)  # Brown wire color
        wire_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        wire_pen.setWidth(2)
        self.scene.addLine(
            well_width / 2,  # Start at center of socket
            socket_y,
            well_width / 2,  # End at center top
            0,
            wire_pen
        )

        # Draw depth markers (scaled)
        for depth_mark in range(0, int(self.max_depth) + 1, 1000):
            y_pos = depth_mark * scale_factor
            self.scene.addLine(well_width, y_pos, well_width + 10, y_pos, QPen(Qt.GlobalColor.black, 1))
            depth_label = self.scene.addText(f"{depth_mark} ft")
            depth_label.setPos(well_width + 15, y_pos - 10)


    def update_illustration(self, depth, wire_left, top_wire, total_fall):
        try:
            self.depth = depth
            self.wire_left = wire_left
            self.top_wire = top_wire
            self.total_fall = total_fall
            self.max_depth = max(depth * 1.2, 5000)
            self.draw_wire()
        except Exception as e:
            print(f"Update error: {e}")

    def draw_wire(self):
        if self.depth <= 0:
            return

        try:
            self.scene.clear()

            # Calculate visible area
            view_rect = self.viewport().rect()
            visible_height = view_rect.height()
            scale_factor = visible_height / self.max_depth

            # Adjust scene rectangle
            well_width = 70
            self.scene.setSceneRect(0, 0, well_width + 150, self.max_depth * scale_factor)

            # Draw well casing
            casing = QGraphicsRectItem(0, 0, well_width, self.max_depth * scale_factor)
            casing.setPen(QPen(Qt.GlobalColor.gray, 2))
            casing.setBrush(QColor(240, 240, 240))
            self.scene.addItem(casing)

            # Draw tubing (smaller rectangle inside casing)
            tubing_width = well_width - 20
            tubing = QGraphicsRectItem(10, 0, tubing_width, self.max_depth * scale_factor)
            tubing.setPen(QPen(Qt.GlobalColor.darkGray, 1))
            tubing.setBrush(Qt.GlobalColor.transparent)
            self.scene.addItem(tubing)

            # Draw wire as a spring/helix
            if self.wire_left > 0:
                wire_top = (self.depth - self.wire_left) * scale_factor
                wire_height = self.wire_left * scale_factor

                # Spring parameters
                spring_width = tubing_width
                spring_radius = spring_width / 2
                center_x = well_width / 2
                coils = max(3, min(30, int(wire_height / 50)))  # Dynamic coil count
                points_per_coil = 10  # More points = smoother spring

                # Create a path for the spring
                path = QPainterPath()

                # Start centered at the rope socket position
                socket_bottom_y = self.depth * scale_factor
                path.moveTo(center_x, socket_bottom_y)

                # Draw multiple points from bottom to top
                for i in range(1, coils * points_per_coil + 1):
                    progress = i / (coils * points_per_coil)
                    angle = 2 * math.pi * coils * (1 - progress)  # Count down from full rotation
                    y = socket_bottom_y - (wire_height * progress)
                    x = center_x + spring_radius * math.cos(angle)

                    # For the last segment, ensure we end at center_x
                    if i == coils * points_per_coil:
                        x = center_x

                    path.lineTo(x, y)

                # Spring appearance
                spring_pen = QPen(QColor(139, 69, 19))  # Brown wire color
                spring_pen.setWidth(2)
                spring_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

                self.scene.addPath(path, spring_pen)

                # Draw fallback effect
                if self.total_fall > 0:
                    fall_y = (self.depth - self.wire_left + self.total_fall) * scale_factor
                    fall_pen = QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine)
                    self.scene.addLine(center_x, wire_top, center_x, fall_y, fall_pen)

                    # Arrow head
                    arrow_poly = QPolygonF([
                        QPointF(center_x - 5, fall_y + 5),
                        QPointF(center_x + 5, fall_y + 5),
                        QPointF(center_x, fall_y)
                    ])
                    arrow_pen = QPen(Qt.GlobalColor.red, 1)
                    self.scene.addPolygon(arrow_poly, arrow_pen, QBrush(Qt.GlobalColor.red))

            # Draw depth markers
            for depth_mark in range(0, int(self.max_depth) + 1, 1000):
                y_pos = depth_mark * scale_factor
                self.scene.addLine(well_width, y_pos, well_width + 10, y_pos, QPen(Qt.GlobalColor.black, 1))
                depth_label = self.scene.addText(f"{depth_mark} ft")
                depth_label.setPos(well_width + 15, y_pos - 10)

            # Labels
            # Rope socket depth
            socket_y = self.depth * scale_factor
            socket_label = self.scene.addText(f"Rope Socket: \n{self.depth} ft")
            socket_label.setPos(well_width + 70, socket_y - 15)
            self.scene.addLine(0, socket_y, well_width, socket_y, QPen(Qt.GlobalColor.blue, 2))

            # Top of wire
            if self.top_wire > 0:
                top_y = self.top_wire * scale_factor
                top_label = self.scene.addText(f"Top of Wire: \n{self.top_wire:.1f} ft")
                top_label.setPos(well_width + 70, top_y - 15)
                self.scene.addLine(0, top_y, well_width, top_y, QPen(Qt.GlobalColor.darkGreen, 2))

            # Fallback label
            if self.total_fall > 0:
                fall_label = self.scene.addText(f"Fallback: \n{self.total_fall:.1f} ft")
                fall_label.setDefaultTextColor(Qt.GlobalColor.darkRed)
                fall_label.setPos(well_width + 70, (self.depth - self.wire_left / 2) * scale_factor)

            # Draw rope socket image at bottom
            if self.depth > 0:
                socket_y = self.depth * scale_factor
                if self.rope_socket_img:
                    # Position so top of image touches bottom of wire
                    socket_img = self.scene.addPixmap(self.rope_socket_img)
                    socket_img.setPos(
                        well_width / 2 - self.rope_socket_img.width() / 2,  # Center horizontally
                        socket_y  # Position top of image at socket depth
                    )
                    socket_img.setZValue(10)  # Make sure it's on top
                else:
                    # Fallback drawing - rectangle with top at socket depth
                    socket = self.scene.addRect(
                        tubing_width / 2 - 15,  # x position
                        socket_y,  # y position (top of rectangle)
                        30,  # width
                        25,  # height
                        QPen(Qt.GlobalColor.darkGray, 2),
                        QBrush(QColor(100, 100, 100))
                    )
                    socket.setZValue(10)

        except Exception as e:
            print(f"Drawing error: {e}")

    def resizeEvent(self, event):
        if self.depth > 0:  # Only redraw if we have data
            self.draw_wire()
        super().resizeEvent(event)

    def copy_to_clipboard(self):
        try:
            # Create a QPixmap to hold the scene image
            rect = self.scene.sceneRect()
            pixmap = QPixmap(rect.size().toSize())
            pixmap.fill(Qt.GlobalColor.white)  # White background

            # Create a QPainter for the pixmap
            painter = QPainter(pixmap)
            painter.setRenderHints(
                QPainter.RenderHint.Antialiasing |
                QPainter.RenderHint.TextAntialiasing |
                QPainter.RenderHint.SmoothPixmapTransform
            )

            # Render the scene onto the pixmap
            self.scene.render(
                painter,
                target=QRectF(pixmap.rect()),  # Target rectangle
                source=rect,  # Source rectangle
                mode=Qt.AspectRatioMode.KeepAspectRatio
            )
            painter.end()

            # Copy to clipboard
            if not pixmap.isNull():
                QApplication.clipboard().setPixmap(pixmap)
                return True
            return False

        except Exception as e:
            print(f"Error copying to clipboard: {str(e)}")
            return False